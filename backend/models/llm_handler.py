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
    GenerationConfig
)
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class LLMHandler:
    """Handles SmolLM2 text generation with streaming"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = os.getenv("LLM_MODEL_NAME", "HuggingFaceTB/SmolLM2-135M-Instruct")
        
        # Generation settings from env
        self.max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "512"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("TOP_P", "0.9"))
        self.do_sample = os.getenv("DO_SAMPLE", "true").lower() == "true"
        
    async def initialize(self):
        """Initialize the model and tokenizer"""
        logger.info(f"🔧 Loading {self.model_name} on {self.device}...")
        
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
                trust_remote_code=True
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True
            ).to(self.device)
            
        logger.info(f"✅ Model loaded successfully on {self.device}")
        logger.info(f"📊 Memory footprint: {self.model.get_memory_footprint() / 1e6:.2f} MB")
    
    def format_chat_prompt(self, user_message: str, system_prompt: str = None) -> str:
        """Format the input as a chat prompt for the instruct model"""
        if system_prompt is None:
            system_prompt = "You are a helpful, friendly, and knowledgeable AI assistant. Provide clear, concise, and accurate responses."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Use the tokenizer's chat template
        formatted_prompt = self.tokenizer.apply_chat_template(
            messages, 
            tokenize=False,
            add_generation_prompt=True
        )
        
        return formatted_prompt
    
    async def generate_stream(self, user_message: str, max_new_tokens: int = 150) -> AsyncGenerator[str, None]:
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
                self.tokenizer, 
                timeout=10.0, 
                skip_prompt=True, 
                skip_special_tokens=True
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
                    accumulated_text += new_text
                    yield new_text
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
                    
            thread.join()
            logger.info(f"📝 Generated {len(accumulated_text)} characters")
            
        except Exception as e:
            logger.error(f"❌ Error in text generation: {e}")
            yield f"Sorry, I encountered an error while generating a response: {str(e)}"
    
    async def generate_complete(self, user_message: str, max_new_tokens: int = 150) -> str:
        """Generate complete response (non-streaming)"""
        accumulated_text = ""
        async for chunk in self.generate_stream(user_message, max_new_tokens):
            accumulated_text += chunk
        return accumulated_text.strip()
