# SpeakStream - Real-time Streaming Chatbot

A web-based chatbot that processes user input using a small, efficient language model and streams both text and audio responses in real-time.

## ✨ Version 1.1.0 - Stable Release

### 🎯 Production Ready Features

- ✅ **Fully functional UI** - Send button, audio indicators, and chat history all working
- ✅ **Robust audio system** - Progressive playback with comprehensive debugging tools
- ✅ **Environment configuration** - Complete configuration via `.env` file
- ✅ **Persistent chat history** - Session restoration with localStorage
- ✅ **Comprehensive debugging** - Audio diagnostics and WebSocket testing tools

### �️ Technical Improvements

- 📁 **Configuration API** - `/config` endpoint for dynamic frontend configuration
- 🎵 **Audio debugging** - Dedicated debug page at `/static/audio-debug.html`
- 🔧 **Enhanced logging** - Detailed debugging throughout the audio pipeline
- 🌐 **WebSocket reliability** - Auto-reconnect and improved error handling
- 💾 **Data persistence** - Configurable chat history limits and storage

## Features

- **Real-time Text Generation**: Uses HuggingFace SmolLM2-135M-Instruct for efficient text generation
- **Progressive Speech Synthesis**: Converts text chunks to audio using Coqui TTS (glow-tts model)
- **Streaming Audio Playback**: Streams audio to frontend for smooth, real-time playback
- **Asynchronous Backend**: FastAPI-based backend with WebSocket support
- **Web Audio API**: Low-latency audio playback in the browser
- **Environment Configuration**: All settings configurable via `.env` file
- **Chat History**: Persistent conversation history with localStorage

## Architecture

```text
Frontend (Web Browser)
├── HTML5 + JavaScript + CSS
├── Configuration loader (config.js)
├── WebSocket connection with auto-reconnect
├── Web Audio API with enhanced debugging
├── Progressive audio buffer management
└── Chat history persistence

Backend (FastAPI)
├── Environment-based configuration
├── WebSocket handler with improved streaming
├── Text streaming with SmolLM2
├── TTS chunking and synthesis
├── Audio streaming optimization
└── Configuration API endpoint
```

## Quick Start

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure settings** (optional):

   Edit `.env` file:

   ```bash
   # Key settings
   PORT=8000
   DEFAULT_VOLUME=0.8
   SAVE_CHAT_HISTORY=true
   MAX_NEW_TOKENS=512
   ```

3. **Start the backend**:

   ```bash
   python backend/main.py
   ```

4. **Open the frontend**:

   Visit <http://localhost:8000> in your browser

5. **Start chatting**:

   - Click "Connect" to establish connection
   - Type a message and press Enter
   - Click anywhere first to enable audio!

## 🔧 Configuration Options

All settings are now configurable via the `.env` file:

```bash
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Model Settings  
LLM_MODEL_NAME=HuggingFaceTB/SmolLM2-135M-Instruct
TTS_MODEL_NAME=tts_models/en/ljspeech/glow-tts
TTS_SAMPLE_RATE=22050

# Audio Settings
DEFAULT_VOLUME=0.8
ENABLE_AUDIO=true
CHUNK_SIZE=1024
MAX_QUEUE_SIZE=10

# UI Settings
AUTO_SCROLL=true
SAVE_CHAT_HISTORY=true
MAX_CHAT_HISTORY=100

# Generation Settings
MAX_NEW_TOKENS=512
TEMPERATURE=0.7
TOP_P=0.9
DO_SAMPLE=true
```

## Technical Details

### Text Generation Strategy

- Uses HuggingFace Transformers with `TextIteratorStreamer`
- Streams tokens in real-time to minimize latency
- Implements smart text chunking based on punctuation and length
- Environment-configurable generation parameters

### Audio Synthesis Pipeline

- Segments streaming text into coherent units for TTS
- Uses Coqui TTS glow-tts model for fast inference
- Converts WAV output to base64 for WebSocket transmission
- Implements audio buffer management for smooth playback
- Enhanced error handling and debugging

### Latency Optimization

- Asynchronous processing pipeline
- Streaming text generation
- Progressive TTS synthesis
- Audio buffer pre-loading
- WebSocket communication with auto-reconnect

### Configuration Management

- Centralized `.env` configuration
- Runtime config loading via `/config` endpoint
- Frontend adapts to backend settings
- No hardcoded values in client code

## Models Used

- **Language Model**: HuggingFaceTB/SmolLM2-135M-Instruct (135M parameters)
- **TTS Model**: tts_models/en/ljspeech/glow-tts
- **Memory Footprint**: ~400MB total

## Performance Characteristics

- **Text Generation**: ~50-100 tokens/second
- **TTS Latency**: ~200-500ms per chunk
- **Audio Buffer**: 2-3 seconds ahead
- **Total Response Time**: <1 second to first audio

## 🐛 Troubleshooting

### Fixed in v1.1.0

- ✅ Send button always disabled → Now works properly
- ✅ Audio indicator stuck → Updates correctly  
- ✅ No chat history → Persistent storage
- ✅ Hardcoded settings → Environment config

### Common Issues

**No Audio**: Click anywhere on the page first to enable audio context

**Connection Issues**: Check if server is running on port 8000

**Debug Tools**:

- Visit `/static/audio-debug.html` for audio testing
- Check browser console (F12) for errors
- Run `python test_websocket.py` for backend testing

## Project Structure

```text
speakstream/
├── 📄 README.md              # This file
├── 📄 QUICKSTART.md          # Quick setup guide
├── 📄 TECHNICAL_DOCS.md      # Detailed technical docs
├── 📄 requirements.txt       # Python dependencies
├── 📄 .env                   # Configuration file
├── 📄 LICENSE                # MIT license
├── 📄 test_websocket.py      # WebSocket test script
├── 
├── 🗂️ backend/               # FastAPI server
│   ├── 🐍 main.py            # Main app with config endpoint
│   ├── 🗂️ models/
│   │   ├── 🐍 llm_handler.py # SmolLM2 (.env configured)
│   │   └── 🐍 tts_handler.py # Coqui TTS (.env configured)
│   ├── 🗂️ utils/
│   │   ├── 🐍 text_chunker.py # Text segmentation
│   │   └── 🐍 audio_utils.py # Audio processing
│   └── 🗂️ websocket/
│       └── 🐍 chat_handler.py # WebSocket (fixed streaming)
├──
└── 🗂️ frontend/              # Web interface
    ├── 📄 index.html         # Main page (config loading)
    ├── 📄 debug.html         # WebSocket debugging tool
    ├── 📄 audio-debug.html   # Audio debugging tool
    ├── 🗂️ css/
    │   └── 📄 style.css      # Styling
    └── 🗂️ js/
        ├── 📄 config.js      # Configuration loader
        ├── 📄 audio-player.js # Web Audio API (enhanced)
        ├── 📄 websocket.js   # WebSocket client (config-aware)
        ├── 📄 ui-fixed.js    # UI controller (production)
        └── 📄 ui.js          # UI controller (development)
```

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)** - Detailed architecture docs
- **`.env`** - Configuration reference with comments

## 🎯 Current Status

**Production Ready** ✅ - All core functionality is working:

- ✅ **Backend**: FastAPI server with WebSocket streaming and configuration API
- ✅ **Models**: SmolLM2-135M-Instruct for text + Coqui TTS for audio synthesis  
- ✅ **Frontend**: Full-featured web UI with audio playback and chat history
- ✅ **Configuration**: Complete `.env` file configuration system
- ✅ **Debugging**: Comprehensive debugging tools and error handling
- ✅ **Documentation**: Complete setup guides and technical documentation

## 🎯 What's Next

- 🎵 Multiple TTS voice options
- 🌍 Multi-language support  
- 💾 Server-side chat persistence
- 🔊 Real-time voice input
- 📱 Mobile app version

---

**🎉 Enjoy real-time AI conversations with SpeakStream!**

Built with ❤️ using open-source models and modern web technologies.
