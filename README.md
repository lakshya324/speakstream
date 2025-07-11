# SpeakStream - Real-time Streaming Chatbot

A web-based chatbot that processes user input using a small, efficient language model and streams both text and audio responses in real-time.

## Features

- **Real-time Text Generation**: Uses HuggingFace SmolLM2-135M-Instruct for efficient text generation
- **Progressive Speech Synthesis**: Converts text chunks to audio using Coqui TTS (glow-tts model)
- **Streaming Audio Playback**: Streams audio to frontend for smooth, real-time playback
- **Asynchronous Backend**: FastAPI-based backend with WebSocket support
- **Web Audio API**: Low-latency audio playback in the browser

## Architecture

```
Frontend (Web Browser)
├── HTML5 + JavaScript
├── WebSocket connection
├── Web Audio API
└── Progressive audio buffer

Backend (FastAPI)
├── WebSocket handler
├── Text streaming with SmolLM2
├── TTS chunking and synthesis
└── Audio streaming
```

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend**:
   ```bash
   python backend/main.py
   ```

3. **Open the frontend**:
   Open `frontend/index.html` in your browser or visit `http://localhost:8000`

## Technical Details

### Text Generation Strategy
- Uses HuggingFace Transformers with `TextIteratorStreamer` 
- Streams tokens in real-time to minimize latency
- Implements smart text chunking based on punctuation and length

### Audio Synthesis Pipeline
- Segments streaming text into coherent units for TTS
- Uses Coqui TTS glow-tts model for fast inference
- Converts WAV output to base64 for WebSocket transmission
- Implements audio buffer management for smooth playback

### Latency Optimization
- Asynchronous processing pipeline
- Streaming text generation
- Progressive TTS synthesis
- Audio buffer pre-loading
- WebSocket communication

## Models Used

- **Language Model**: HuggingFaceTB/SmolLM2-135M-Instruct (135M parameters)
- **TTS Model**: tts_models/en/ljspeech/glow-tts
- **Memory Footprint**: ~400MB total

## Performance Characteristics

- **Text Generation**: ~50-100 tokens/second
- **TTS Latency**: ~200-500ms per chunk
- **Audio Buffer**: 2-3 seconds ahead
- **Total Response Time**: <1 second to first audio

## Project Structure

```
speakstream/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   ├── llm_handler.py   # SmolLM2 text generation
│   │   └── tts_handler.py   # Coqui TTS synthesis
│   ├── utils/
│   │   ├── text_chunker.py  # Text segmentation
│   │   └── audio_utils.py   # Audio processing
│   └── websocket/
│       └── chat_handler.py  # WebSocket management
├── frontend/
│   ├── index.html           # Main interface
│   ├── js/
│   │   ├── audio-player.js  # Web Audio API handler
│   │   ├── websocket.js     # WebSocket client
│   │   └── ui.js           # User interface
│   └── css/
│       └── style.css        # Styling
└── requirements.txt         # Python dependencies
```
