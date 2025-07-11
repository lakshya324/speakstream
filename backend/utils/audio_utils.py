"""
Audio processing utilities
"""
import base64
import io
import numpy as np
import soundfile as sf
from typing import Optional

class AudioUtils:
    """Utilities for audio processing and conversion"""
    
    @staticmethod
    def numpy_to_base64_wav(audio_array: np.ndarray, sample_rate: int = 22050) -> str:
        """Convert numpy audio array to base64 encoded WAV"""
        try:
            # Ensure audio is in the right format
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)
            
            # Normalize if needed
            if np.max(np.abs(audio_array)) > 1.0:
                audio_array = audio_array / np.max(np.abs(audio_array))
            
            # Create in-memory buffer
            buffer = io.BytesIO()
            
            # Write as WAV
            sf.write(buffer, audio_array, sample_rate, format='WAV', subtype='PCM_16')
            
            # Get bytes and encode
            audio_bytes = buffer.getvalue()
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            
            return base64_audio
            
        except Exception as e:
            print(f"Error converting audio to base64: {e}")
            return ""
    
    @staticmethod
    def base64_to_numpy(base64_audio: str) -> Optional[tuple]:
        """Convert base64 WAV to numpy array"""
        try:
            # Decode base64
            audio_bytes = base64.b64decode(base64_audio)
            
            # Create buffer and read
            buffer = io.BytesIO(audio_bytes)
            audio_array, sample_rate = sf.read(buffer)
            
            return audio_array, sample_rate
            
        except Exception as e:
            print(f"Error converting base64 to audio: {e}")
            return None
    
    @staticmethod
    def estimate_audio_duration(base64_audio: str) -> float:
        """Estimate audio duration in seconds"""
        try:
            result = AudioUtils.base64_to_numpy(base64_audio)
            if result:
                audio_array, sample_rate = result
                return len(audio_array) / sample_rate
        except:
            pass
        return 0.0
    
    @staticmethod
    def create_silence(duration_seconds: float, sample_rate: int = 22050) -> str:
        """Create silence audio as base64 WAV"""
        try:
            samples = int(duration_seconds * sample_rate)
            silence = np.zeros(samples, dtype=np.float32)
            return AudioUtils.numpy_to_base64_wav(silence, sample_rate)
        except:
            return ""
    
    @staticmethod
    def concatenate_audio_base64(audio_chunks: list, sample_rate: int = 22050) -> str:
        """Concatenate multiple base64 audio chunks"""
        try:
            audio_arrays = []
            
            for chunk in audio_chunks:
                result = AudioUtils.base64_to_numpy(chunk)
                if result:
                    audio_array, _ = result
                    audio_arrays.append(audio_array)
            
            if audio_arrays:
                combined = np.concatenate(audio_arrays)
                return AudioUtils.numpy_to_base64_wav(combined, sample_rate)
                
        except Exception as e:
            print(f"Error concatenating audio: {e}")
        
        return ""
