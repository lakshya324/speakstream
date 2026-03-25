"""
TTS Handler for Coqui TTS with streaming support
"""
import asyncio
import logging
import base64
import io
import numpy as np
import soundfile as sf
from TTS.api import TTS
import torch
from typing import AsyncGenerator, Dict, Any
from utils.config_manager import config_manager

logger = logging.getLogger(__name__)

class TTSHandler:
    """Handles text-to-speech conversion with Coqui TTS"""
    
    def __init__(self):
        self.tts = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = None
        self.sample_rate = None
        self.chunk_size = None
        self.speaker = None
        self.is_initialized = False
        
        # Initialize configuration from config manager
        self.update_config(config_manager.get_all())
        
        # Register for configuration updates
        config_manager.add_reload_callback(self.on_config_reload)
    def update_config(self, config: Dict[str, Any]):
        """Update configuration settings"""
        self.model_name = config.get("TTS_MODEL_NAME", "tts_models/en/ljspeech/glow-tts")
        self.sample_rate = config.get("TTS_SAMPLE_RATE", 22050)
        self.chunk_size = config.get("CHUNK_SIZE", 1024)
        self.speaker = config.get("TTS_SPEAKER", None)
        
        logger.info(f"🔄 TTS config updated - Model: {self.model_name}, Sample Rate: {self.sample_rate}, Chunk Size: {self.chunk_size}, Speaker: {self.speaker}")
    
    async def on_config_reload(self, config: Dict[str, Any]):
        """Handle configuration reload"""
        old_model_name = self.model_name
        old_sample_rate = self.sample_rate
        self.update_config(config)
        
        # If model name or sample rate changed, we need to reinitialize
        if (old_model_name != self.model_name or old_sample_rate != self.sample_rate) and self.is_initialized:
            logger.info(f"🔄 TTS model or settings changed, reinitializing...")
            await self.initialize()
        else:
            logger.info("🔄 TTS settings updated without model reload")
        
    async def initialize(self):
        """Initialize the TTS model"""
        logger.info(f"\033[36m🔧 Loading TTS model {self.model_name} on {self.device}...\033[0m")
        
        try:
            # Initialize TTS with the glow-tts model
            self.tts = TTS(model_name=self.model_name).to(self.device)
            logger.info(f"✅ TTS model loaded successfully on {self.device}")
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to load TTS model: {e}")
            raise
    
    def audio_to_base64(self, audio_array: np.ndarray) -> str:
        """Convert audio array to base64 encoded WAV"""
        try:
            # Ensure we have a valid audio array
            if audio_array is None or len(audio_array) == 0:
                logger.warning("⚠️ Empty audio array, generating silent audio")
                audio_array = np.zeros(int(self.sample_rate * 0.1), dtype=np.float32)
            
            # Ensure proper shape (1D array)
            if len(audio_array.shape) > 1:
                audio_array = audio_array.squeeze()
            
            # Ensure proper data type
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)
            
            # Ensure proper range [-1, 1]
            if np.max(np.abs(audio_array)) > 1.0:
                audio_array = audio_array / np.max(np.abs(audio_array))
            
            logger.info(f"🎵 Converting audio to WAV: {len(audio_array)} samples at {self.sample_rate}Hz")
            
            # Create an in-memory bytes buffer
            buffer = io.BytesIO()
            
            # Write audio as WAV to buffer with proper parameters
            sf.write(buffer, audio_array, self.sample_rate, format='WAV', subtype='PCM_16')
            
            # Get bytes and encode as base64
            audio_bytes = buffer.getvalue()
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            
            logger.info(f"✅ Audio converted: {len(audio_bytes)} bytes -> {len(base64_audio)} chars base64")
            return base64_audio
            
        except Exception as e:
            logger.error(f"❌ Error converting audio to base64: {e}")
            return ""
    
    async def synthesize_text(self, text: str) -> str:
        """Synthesize text to speech and return base64 encoded audio"""
        try:
            if not text.strip():
                return ""
                
            logger.info(f"🔊 Synthesizing: '{text[:30]}...'")
            
            # Run TTS synthesis in executor to avoid blocking
            loop = asyncio.get_event_loop()
            def _synthesize():
                try:
                    # For VCTK model, we need to specify a speaker
                    if "vctk" in self.model_name.lower():
                        if self.speaker:
                            logger.info(f"🎤 Using VCTK speaker: {self.speaker}")
                            wav = self.tts.tts(text=text.strip(), speaker=self.speaker)
                        else:
                            # Default to a common VCTK speaker if none specified
                            default_speaker = "p273"
                            logger.info(f"🎤 Using default VCTK speaker: {default_speaker}")
                            wav = self.tts.tts(text=text.strip(), speaker=default_speaker)
                    else:
                        # For other models, try with speaker if available, otherwise without
                        if self.speaker and hasattr(self.tts, 'speakers') and self.tts.speakers:
                            wav = self.tts.tts(text=text.strip(), speaker=self.speaker)
                        else:
                            wav = self.tts.tts(text=text.strip())
                    
                    # Ensure we get a numpy array
                    if isinstance(wav, list):
                        wav = np.array(wav)
                    elif not isinstance(wav, np.ndarray):
                        wav = np.array(wav)
                    
                    # Ensure proper data type and range
                    if wav.dtype != np.float32:
                        wav = wav.astype(np.float32)
                    
                    # Normalize audio if needed
                    if np.max(np.abs(wav)) > 1.0:
                        wav = wav / np.max(np.abs(wav))
                    
                    logger.info(f"🎵 Generated audio: shape={wav.shape}, dtype={wav.dtype}, range=[{wav.min():.3f}, {wav.max():.3f}]")
                    return wav
                    
                except Exception as e:
                    logger.error(f"❌ TTS synthesis error: {e}")
                    # Return silent audio as fallback
                    return np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)

            # Run synthesis in thread pool
            audio_array = await loop.run_in_executor(None, _synthesize)
            
            # Convert to base64
            base64_audio = self.audio_to_base64(audio_array)
            
            logger.info(f"✅ Synthesized {len(text)} characters -> {len(base64_audio)} bytes base64")
            return base64_audio
            
        except Exception as e:
            logger.error(f"❌ Error in TTS synthesis: {e}")
            return ""
    
    async def synthesize_stream(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[dict, None]:
        """Process streaming text and yield audio chunks"""
        text_buffer = ""
        chunk_count = 0
        
        try:
            async for text_chunk in text_stream:
                text_buffer += text_chunk
                
                # Check if we have enough text to synthesize
                if self._should_synthesize(text_buffer):
                    # Extract text to synthesize
                    text_to_synthesize, remaining_text = self._extract_synthesis_text(text_buffer)
                    
                    if text_to_synthesize:
                        # Synthesize audio
                        base64_audio = await self.synthesize_text(text_to_synthesize)
                        
                        if base64_audio:
                            chunk_count += 1
                            yield {
                                "type": "audio",
                                "data": base64_audio,
                                "text": text_to_synthesize,
                                "chunk_id": chunk_count
                            }
                        
                        # Update buffer with remaining text
                        text_buffer = remaining_text
                
                # Also yield the text chunk for real-time display
                yield {
                    "type": "text",
                    "data": text_chunk,
                    "chunk_id": chunk_count
                }
            
            # Synthesize any remaining text
            if text_buffer.strip():
                base64_audio = await self.synthesize_text(text_buffer.strip())
                if base64_audio:
                    chunk_count += 1
                    yield {
                        "type": "audio",
                        "data": base64_audio,
                        "text": text_buffer.strip(),
                        "chunk_id": chunk_count
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error in streaming synthesis: {e}")
            yield {
                "type": "error", 
                "data": f"TTS error: {str(e)}"
            }
    
    def _should_synthesize(self, text: str) -> bool:
        """Determine if we have enough text to synthesize"""
        # Synthesize if we have:
        # 1. A complete sentence (ends with punctuation)
        # 2. A long enough chunk (>50 characters)
        # 3. A natural break point
        
        if len(text) < 10:  # Too short
            return False
            
        # Check for sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        for ending in sentence_endings:
            if ending in text:
                return True
        
        # Check for other natural breaks
        natural_breaks = [', ', '; ', ' - ', ' — ']
        if len(text) > 30:
            for break_point in natural_breaks:
                if break_point in text:
                    return True
        
        # Synthesize if too long (avoid very long chunks)
        if len(text) > 80:
            return True
            
        return False
    
    def _extract_synthesis_text(self, text: str) -> tuple[str, str]:
        """Extract text to synthesize and return remaining text"""
        # Find the best break point
        sentence_endings = ['. ', '! ', '? ']
        
        # Look for sentence endings first
        best_pos = -1
        for ending in sentence_endings:
            pos = text.rfind(ending)
            if pos > best_pos:
                best_pos = pos + len(ending)
        
        if best_pos > 0:
            return text[:best_pos].strip(), text[best_pos:].strip()
        
        # Look for other natural breaks
        natural_breaks = [', ', '; ', ' - ', ' — ']
        if len(text) > 30:
            for break_point in natural_breaks:
                pos = text.rfind(break_point)
                if pos > 0 and pos > best_pos:
                    best_pos = pos + len(break_point)
        
        if best_pos > 0:
            return text[:best_pos].strip(), text[best_pos:].strip()
        
        # If no good break point and text is long, split at word boundary
        if len(text) > 80:
            words = text.split()
            mid_point = len(words) // 2
            synthesis_text = ' '.join(words[:mid_point])
            remaining_text = ' '.join(words[mid_point:])
            return synthesis_text.strip(), remaining_text.strip()
        
        # Return all text if short enough
        return text.strip(), ""
