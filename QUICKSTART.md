# 🎤 SpeakStream - Quick Start Guide

## What is SpeakStream?

SpeakStream is a real-time streaming chatbot that generates both text and audio responses simultaneously. It uses:

- **SmolLM2-135M-Instruct** for fast, efficient text generation
- **Coqui TTS (glow-tts)** for high-quality speech synthesis
- **FastAPI + WebSocket** for real-time communication
- **Web Audio API** for low-latency audio playback

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Test Setup (Optional)

```bash
# Run component tests
python demo.py
```

### 3. Start the Server

```bash
# Method 1: Direct
python backend/main.py

# Method 2: With script
chmod +x start.sh
./start.sh

# Method 3: VS Code task
# Press Ctrl/Cmd+Shift+P, type "Tasks: Run Task", select "Start SpeakStream Server"
```

### 4. Open the Frontend

- **Automatic**: Visit http://localhost:8000 in your browser
- **Manual**: Open `frontend/index.html` directly

### 5. Start Chatting!

1. Click "Connect" to establish WebSocket connection
2. Type a message and press Enter or click "Send"
3. Watch as the AI generates text in real-time
4. Listen to the voice synthesis as it speaks the response

## 📁 Project Structure

```
speakstream/
├── 📄 README.md              # Main documentation
├── 📄 requirements.txt       # Python dependencies
├── 📄 demo.py                # Test script
├── 📄 setup_dev.py           # Development setup
├── 📄 start.sh               # Startup script
├── 📄 TECHNICAL_DOCS.md      # Detailed technical docs
├── 
├── 🗂️ backend/               # FastAPI server
│   ├── 🐍 main.py            # Main application
│   ├── 🗂️ models/
│   │   ├── 🐍 llm_handler.py # SmolLM2 integration
│   │   └── 🐍 tts_handler.py # Coqui TTS integration
│   ├── 🗂️ utils/
│   │   ├── 🐍 text_chunker.py # Text processing
│   │   └── 🐍 audio_utils.py # Audio utilities
│   └── 🗂️ websocket/
│       └── 🐍 chat_handler.py # WebSocket management
├──
└── 🗂️ frontend/              # Web interface
    ├── 📄 index.html         # Main page
    ├── 🗂️ css/
    │   └── 📄 style.css      # Styling
    └── 🗂️ js/
        ├── 📄 audio-player.js # Web Audio API
        ├── 📄 websocket.js   # WebSocket client
        └── 📄 ui-fixed.js    # UI controller
```

## ⚡ Key Features

### Real-time Streaming
- Text appears as the AI generates it (token by token)
- Audio synthesis happens in parallel
- No waiting for complete responses

### Smart Audio Chunking
- Segments text at natural breaks (sentences, phrases)
- Balances audio quality with responsiveness
- Handles streaming text intelligently

### Web Audio Integration
- Low-latency audio playback
- Buffer management for smooth streaming
- Volume control and mute functionality

### Modern Web UI
- Responsive design
- Real-time status indicators
- Debug information panel
- Mobile-friendly interface

## 🔧 Configuration Options

### Model Settings (in backend/models/)

**LLM Configuration**:
```python
# In llm_handler.py
max_new_tokens = 150        # Response length
temperature = 0.7           # Creativity (0.1-1.0)
top_p = 0.9                # Nucleus sampling
```

**TTS Configuration**:
```python
# In tts_handler.py
min_chunk_size = 10         # Minimum text chunk
max_chunk_size = 100        # Maximum text chunk
sample_rate = 22050         # Audio quality
```

### Server Settings (in backend/main.py)

```python
host = "0.0.0.0"           # Server host
port = 8000                # Server port
reload = True              # Development mode
```

## 🎯 Usage Tips

### For Best Performance
1. **Hardware**: 2GB+ RAM recommended
2. **Network**: Stable internet for model downloads
3. **Browser**: Chrome/Edge for best Web Audio support
4. **Audio**: Use headphones to prevent feedback

### Prompt Engineering
- **Short queries**: Get faster responses
- **Clear instructions**: "Explain in simple terms..."
- **Specific requests**: "Write a 2-sentence summary..."

### Audio Quality
- **Punctuation matters**: Use periods, commas for natural pauses
- **Sentence structure**: Shorter sentences = better chunking
- **Volume control**: Adjust in the UI or browser

## 🐛 Troubleshooting

### Common Issues

**"Connection failed"**:
- Check if server is running on port 8000
- Try restarting the backend server
- Check firewall settings

**"No audio"**:
- Click anywhere to initialize audio context
- Check browser audio permissions
- Verify audio device is connected
- Try refreshing the page

**"Models not loading"**:
- Ensure stable internet connection
- Check available disk space (5GB+ recommended)
- Try: `pip install --upgrade transformers TTS`

**"Slow responses"**:
- Reduce `max_new_tokens` in LLM settings
- Close other applications using GPU/CPU
- Consider using smaller model variants

### Getting Help

1. **Check logs**: Server console shows detailed error messages
2. **Browser console**: F12 → Console for frontend errors
3. **Test components**: Run `python demo.py` to isolate issues
4. **Check dependencies**: Ensure all packages are installed

## 🚀 What's Next?

### Immediate Improvements
1. **Try different prompts** to see how the AI responds
2. **Adjust audio settings** for your preference
3. **Test on mobile devices** for responsive design
4. **Monitor performance** with the debug panel

### Potential Extensions
1. **Voice selection**: Multiple TTS voices
2. **Language support**: Multi-lingual capabilities
3. **Conversation memory**: Chat history persistence
4. **Custom models**: Different LLMs or TTS models
5. **API integration**: External service connections

### Advanced Usage
1. **Model quantization**: Reduce memory usage
2. **Custom training**: Fine-tune on specific domains
3. **Deployment**: Production server setup
4. **Scaling**: Multiple concurrent users

## 📖 Additional Resources

- **Technical Documentation**: See `TECHNICAL_DOCS.md`
- **Model Info**: 
  - [SmolLM2 on Hugging Face](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct)
  - [Coqui TTS Documentation](https://github.com/coqui-ai/TTS)
- **Web Audio API**: [MDN Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

---

**🎉 Enjoy your real-time AI conversations with SpeakStream!**

Built with ❤️ using open-source models and modern web technologies.
