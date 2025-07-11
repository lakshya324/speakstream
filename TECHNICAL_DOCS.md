# SpeakStream Technical Documentation

## Architecture Overview

SpeakStream is a real-time streaming chatbot that combines text generation with speech synthesis for immediate audio feedback. The system uses a modern web architecture with WebSocket communication for low-latency streaming.

### System Components

#### Backend (FastAPI + WebSocket)
- **FastAPI Server**: Handles HTTP requests and WebSocket connections
- **LLM Handler**: Manages SmolLM2-135M-Instruct for text generation
- **TTS Handler**: Manages Coqui TTS for speech synthesis
- **Chat Handler**: Orchestrates communication between LLM and TTS
- **WebSocket Manager**: Handles real-time bidirectional communication

#### Frontend (Vanilla JavaScript)
- **Audio Player**: Web Audio API integration for low-latency playback
- **WebSocket Client**: Manages server communication
- **UI Controller**: Handles user interactions and display
- **Real-time Message Display**: Progressive text and audio rendering

### Data Flow

```
User Input → WebSocket → LLM Streaming → Text Chunking → TTS Synthesis → Audio Streaming → Web Audio API → Speaker Output
                ↓
    Real-time Text Display ← Text Chunks ← WebSocket ← Backend Processing
```

## Key Technical Decisions

### 1. Streaming Text Generation
**Choice**: HuggingFace `TextIteratorStreamer`
- **Why**: Provides token-level streaming with minimal latency
- **Implementation**: Runs in separate thread to avoid blocking
- **Benefit**: User sees response building in real-time

### 2. Text Chunking Strategy
**Choice**: Punctuation and length-based segmentation
- **Why**: Balances audio quality with responsiveness
- **Rules**:
  - Minimum chunk: 10 characters
  - Maximum chunk: 100 characters
  - Prefer sentence endings (. ! ?)
  - Use phrase breaks (, ; -) for longer text
  - Force breaks at word boundaries if too long

### 3. Audio Synthesis Pipeline
**Choice**: Coqui TTS with glow-tts model
- **Why**: Good balance of quality, speed, and resource usage
- **Format**: WAV → Base64 encoding for WebSocket transmission
- **Streaming**: Process chunks as they become available

### 4. Frontend Audio Handling
**Choice**: Web Audio API with buffer management
- **Why**: Lower latency than HTML5 audio elements
- **Implementation**: 
  - AudioContext for precise timing
  - GainNode for volume control
  - Buffer queue for smooth playback
  - Automatic cleanup of old audio chunks

### 5. Communication Protocol
**Choice**: WebSocket with JSON messaging
- **Why**: Bidirectional, low-latency, event-driven
- **Message Types**:
  - `chat`: User text input
  - `response_start`: Begin response generation
  - `chunk`: Text or audio data
  - `response_complete`: End of response
  - `error`: Error messages
  - `ping/pong`: Connection health

## Performance Optimizations

### Backend Optimizations
1. **Async Processing**: All I/O operations are asynchronous
2. **Model Caching**: Models loaded once at startup
3. **Thread Pool**: TTS synthesis in executor threads
4. **Memory Management**: Regular cleanup of audio buffers
5. **Efficient Encoding**: Base64 encoding for audio transmission

### Frontend Optimizations
1. **Audio Buffer Queue**: Maintains 2-3 seconds of audio ahead
2. **Progressive Loading**: Audio plays while text is still generating
3. **Memory Cleanup**: Removes old audio chunks automatically
4. **Debounced Updates**: Limits UI update frequency
5. **Lazy Initialization**: Audio context starts on user interaction

### Network Optimizations
1. **WebSocket Compression**: Reduces bandwidth usage
2. **Chunked Transmission**: Sends data as soon as available
3. **Binary Encoding**: Base64 for efficient audio transfer
4. **Connection Pooling**: Reuses WebSocket connections

## Model Selection Rationale

### SmolLM2-135M-Instruct
**Pros**:
- Small memory footprint (~300MB)
- Fast inference (~50-100 tokens/second)
- Good instruction following
- Apache 2.0 license

**Cons**:
- Limited knowledge cutoff
- Shorter context window
- May struggle with complex reasoning

**Alternative Considerations**:
- SmolLM2-360M: Better quality, higher resource usage
- SmolLM2-1.7B: Best quality, requires more VRAM

### Coqui TTS glow-tts
**Pros**:
- Fast synthesis (~200-500ms per chunk)
- Good English quality
- Moderate resource usage
- Open source

**Cons**:
- English only
- Fixed voice
- No real-time voice cloning

**Alternative Considerations**:
- XTTS: Multi-lingual, voice cloning, but slower
- Bark: More natural, but much slower
- FastSpeech2: Faster, but lower quality

## Latency Analysis

### Target Performance
- **First Token**: < 500ms
- **First Audio**: < 1000ms
- **Audio Buffer**: 2-3 seconds ahead
- **Total Response Time**: < 2 seconds for short queries

### Measured Latencies (approximate)
1. **Text Generation**: 50-200ms per chunk
2. **Text-to-Speech**: 200-500ms per chunk
3. **Audio Encoding**: 10-50ms per chunk
4. **Network Transfer**: 10-100ms per chunk
5. **Audio Decoding**: 5-20ms per chunk
6. **Audio Playback**: Near real-time

### Bottleneck Identification
1. **TTS Synthesis**: Usually the slowest component
2. **Model Loading**: One-time startup cost
3. **Network**: Depends on connection quality
4. **Audio Context**: Browser-dependent initialization

## Scalability Considerations

### Current Limitations
- Single-threaded TTS synthesis
- Models loaded in memory (not shared)
- No request queuing
- No horizontal scaling

### Potential Improvements
1. **Model Sharing**: Load models once, share across requests
2. **Request Queuing**: Handle multiple simultaneous users
3. **TTS Batching**: Process multiple chunks together
4. **Model Quantization**: Reduce memory usage
5. **Distributed Architecture**: Separate LLM and TTS services

## Security Considerations

### Input Validation
- Text length limits
- Rate limiting
- WebSocket connection limits
- Input sanitization

### Model Safety
- No fine-tuning on user data
- Content filtering (basic)
- No persistent user data
- Temporary session storage only

### Network Security
- HTTPS/WSS in production
- CORS policy configuration
- No sensitive data transmission
- Connection timeout handling

## Troubleshooting Guide

### Common Issues

#### "Models not loading"
- Check available RAM (need ~1GB)
- Verify internet connection for downloads
- Check disk space for model cache
- Try clearing transformers cache

#### "Audio not playing"
- Check browser audio permissions
- Verify Web Audio API support
- Test with different browsers
- Check audio device connections

#### "Connection issues"
- Verify WebSocket URL
- Check firewall settings
- Test network connectivity
- Monitor server logs

#### "Slow performance"
- Check CPU/GPU usage
- Monitor memory usage
- Reduce max_new_tokens
- Consider model quantization

### Debugging Tools

#### Backend Logging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python backend/main.py
```

#### Frontend Console
```javascript
// Check audio state
audioPlayer.getState()

// Check WebSocket state
wsClient.getState()

// Monitor audio queue
setInterval(() => console.log(audioPlayer.getQueueLength()), 1000)
```

#### Performance Monitoring
- Browser DevTools Performance tab
- Network tab for WebSocket messages
- Memory tab for leak detection
- Console for error messages

## Future Enhancements

### Planned Features
1. **Voice Selection**: Multiple TTS voices
2. **Language Support**: Multi-lingual capabilities
3. **Voice Cloning**: User voice customization
4. **Model Selection**: Choose different LLMs
5. **Conversation History**: Persistent chat history

### Technical Improvements
1. **Model Quantization**: Reduce memory usage
2. **Streaming TTS**: Real-time audio synthesis
3. **Better Chunking**: Semantic text segmentation
4. **Caching Layer**: Cache common responses
5. **Load Balancing**: Multiple server instances

### UI/UX Enhancements
1. **Mobile Support**: Responsive design
2. **Dark Mode**: Theme customization
3. **Accessibility**: Screen reader support
4. **Customization**: User preferences
5. **Analytics**: Usage statistics

## Development Setup

### Prerequisites
- Python 3.9+
- 2GB+ RAM
- 5GB+ disk space (for models)
- Modern web browser

### Quick Start
```bash
# Clone and setup
git clone <repository>
cd speakstream

# Install dependencies
pip install -r requirements.txt

# Run development server
python setup_dev.py
python backend/main.py

# Open frontend
open http://localhost:8000
```

### Development Commands
```bash
# Start backend with hot reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run with debug logging
LOG_LEVEL=DEBUG python backend/main.py

# Test model loading
python -c "from backend.models.llm_handler import LLMHandler; h = LLMHandler(); h.initialize()"
```

This documentation provides comprehensive technical details for developers working on SpeakStream.
