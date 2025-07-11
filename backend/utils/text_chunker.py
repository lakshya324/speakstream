"""
Text chunking utilities for optimal TTS processing
"""
import re
from typing import List, Tuple

class TextChunker:
    """Handles intelligent text chunking for TTS"""
    
    def __init__(self, min_chunk_size: int = 10, max_chunk_size: int = 100):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Define sentence boundaries
        self.sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n', '.', '!', '?']
        self.phrase_boundaries = [', ', '; ', ' - ', ' — ', ': ', ' and ', ' but ', ' or ']
        
    def chunk_text(self, text: str) -> List[str]:
        """Split text into optimal chunks for TTS"""
        if not text.strip():
            return []
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            # If adding this sentence would make chunk too long, finalize current chunk
            if current_chunk and len(current_chunk + sentence) > self.max_chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence
            
            # If current chunk is long enough and ends well, finalize it
            if (len(current_chunk) >= self.min_chunk_size and 
                self._ends_well(current_chunk)):
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        # Add any remaining text
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Use regex to split on sentence boundaries while preserving them
        pattern = r'([.!?]+\s*)'
        parts = re.split(pattern, text)
        
        sentences = []
        current = ""
        
        for part in parts:
            current += part
            if re.match(r'[.!?]+\s*$', part):
                if current.strip():
                    sentences.append(current)
                current = ""
        
        if current.strip():
            sentences.append(current)
        
        return sentences
    
    def _ends_well(self, text: str) -> bool:
        """Check if text ends at a good boundary"""
        text = text.strip()
        if not text:
            return False
        
        # Good if ends with sentence punctuation
        if any(text.endswith(ending.strip()) for ending in self.sentence_endings):
            return True
        
        # Good if ends with phrase boundary and is long enough
        if len(text) > self.min_chunk_size * 2:
            if any(ending.strip() in text[-10:] for ending in self.phrase_boundaries):
                return True
        
        return False
    
    def chunk_streaming_text(self, text_buffer: str) -> Tuple[str, str]:
        """
        Extract chunkable text from streaming buffer
        Returns: (text_to_synthesize, remaining_text)
        """
        if len(text_buffer) < self.min_chunk_size:
            return "", text_buffer
        
        # Look for good breaking points
        best_break = -1
        
        # Prefer sentence endings
        for ending in self.sentence_endings:
            pos = text_buffer.rfind(ending)
            if pos > best_break and pos >= self.min_chunk_size:
                best_break = pos + len(ending)
        
        # If no sentence ending, look for phrase boundaries
        if best_break == -1 and len(text_buffer) > self.min_chunk_size * 2:
            for boundary in self.phrase_boundaries:
                pos = text_buffer.rfind(boundary)
                if pos > best_break and pos >= self.min_chunk_size:
                    best_break = pos + len(boundary)
        
        # If text is too long, force a break at word boundary
        if best_break == -1 and len(text_buffer) > self.max_chunk_size:
            words = text_buffer.split()
            mid_point = len(words) // 2
            if mid_point > 0:
                chunk_text = ' '.join(words[:mid_point])
                remaining_text = ' '.join(words[mid_point:])
                return chunk_text, remaining_text
        
        if best_break > 0:
            return text_buffer[:best_break].strip(), text_buffer[best_break:].strip()
        
        return "", text_buffer
