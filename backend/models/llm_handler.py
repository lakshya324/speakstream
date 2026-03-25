"""
LLM Handler for SmolLM2-135M-Instruct model
Handles text generation with streaming support
"""

import asyncio
import logging
import os
import torch
from threading import Thread
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
    GenerationConfig,
)
from typing import AsyncGenerator, Dict, Any
from utils.config_manager import config_manager

logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles SmolLM2 text generation with streaming"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = None
        self.is_initialized = False

        # Initialize configuration from config manager
        self.update_config(config_manager.get_all())

        # Register for configuration updates
        config_manager.add_reload_callback(self.on_config_reload)

    def update_config(self, config: Dict[str, Any]):
        """Update configuration settings"""
        self.model_name = config.get("LLM_MODEL_NAME")
        self.max_new_tokens = config.get("MAX_NEW_TOKENS", 512)
        self.temperature = config.get("TEMPERATURE", 0.7)
        self.top_p = config.get("TOP_P", 0.9)
        self.do_sample = config.get("DO_SAMPLE", True)

        logger.info(
            f"🔄 LLM config updated - Model: {self.model_name}, Tokens: {self.max_new_tokens}, Temp: {self.temperature}"
        )

    async def on_config_reload(self, config: Dict[str, Any]):
        """Handle configuration reload"""
        old_model_name = self.model_name
        self.update_config(config)

        # If model name changed, we need to reinitialize
        if old_model_name != self.model_name and self.is_initialized:
            logger.info(
                f"🔄 Model changed from {old_model_name} to {self.model_name}, reinitializing..."
            )
            await self.initialize()
        else:
            logger.info("🔄 LLM generation settings updated without model reload")

    async def initialize(self):
        """Initialize the model and tokenizer"""
        logger.info(f"\033[96m🔧 Loading {self.model_name} on {self.device}...\033[0m")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with appropriate precision
        if self.device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, trust_remote_code=True
            ).to(self.device)

        logger.info(f"✅ Model loaded successfully on {self.device}")
        logger.info(
            f"📊 Memory footprint: {self.model.get_memory_footprint() / 1e6:.2f} MB"
        )
        self.is_initialized = True

    def format_chat_prompt(self, user_message: str, system_prompt: str = None) -> str:
        """Format the input as a chat prompt for the instruct model"""
        if system_prompt is None:
            system_prompt = """You are Sharon, a helpful customer support executive at RAM Bank. A customer named Darshil is having trouble logging into his netbanking. 

Respond as Sharon in a natural conversation. Be helpful, professional, and provide clear troubleshooting steps."""

        # Create proper message structure
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Use the tokenizer's chat template to format properly
        try:
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            return formatted_prompt
        except Exception as e:
            logger.warning(f"⚠️ Chat template failed: {e}")
            # For Gemma-style models, combine system and user message
            combined_message = f"{system_prompt}\n\nUser: {user_message}"
            fallback_messages = [{"role": "user", "content": combined_message}]
            try:
                return self.tokenizer.apply_chat_template(
                    fallback_messages, tokenize=False, add_generation_prompt=True
                )
            except Exception as e2:
                logger.error(f"❌ Both chat templates failed: {e2}")
                # Manual fallback for Gemma
                return f"<bos><start_of_turn>user\n{combined_message}<end_of_turn>\n<start_of_turn>model\n"

    async def generate_stream(
        self, user_message: str, max_new_tokens: int = 150
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from the model"""
        try:
            # Format the prompt
            prompt = self.format_chat_prompt(user_message)

            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)

            # Set up generation config
            generation_config = GenerationConfig(
                max_new_tokens=max_new_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=self.do_sample,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

            # Create text streamer
            streamer = TextIteratorStreamer(
                self.tokenizer, timeout=10.0, skip_prompt=True, skip_special_tokens=True
            )

            # Run generation in a separate thread
            generation_kwargs = dict(
                inputs=inputs,
                generation_config=generation_config,
                streamer=streamer,
            )

            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()

            # Stream the generated text
            accumulated_text = ""

            for new_text in streamer:
                if new_text:
                    # Check for role markers that should be filtered
                    role_markers = [
                        "<|user|>",
                        "<|system|>",
                        "<|assistant|>",
                        "<|end|>",
                    ]
                    if any(marker in new_text.lower() for marker in role_markers):
                        continue

                    # Filter out any thinking tags if they appear
                    # if "<think>" in new_text.lower() or "</think>" in new_text.lower():
                    #     continue

                    # Yield clean text
                    if new_text.strip():
                        accumulated_text += new_text
                        yield new_text

                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)

            thread.join()
            logger.info(f"📝 Generated {len(accumulated_text)} characters")

        except Exception as e:
            logger.error(f"❌ Error in text generation: {e}")
            yield f"Sorry, I encountered an error while generating a response: {str(e)}"

    async def generate_complete(
        self, user_message: str, max_new_tokens: int = 150
    ) -> str:
        """Generate complete response (non-streaming)"""
        accumulated_text = ""
        async for chunk in self.generate_stream(user_message, max_new_tokens):
            accumulated_text += chunk
        return accumulated_text.strip()
