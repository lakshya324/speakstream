# Auto-Reload Configuration Feature

## Overview

SpeakStream now includes automatic configuration reloading! When you modify the `.env` file, all changes are automatically applied without needing to restart the application.

## How It Works

1. **File Watcher**: Monitors the `.env` file for changes using the `watchdog` library
2. **Configuration Manager**: Centralized config management with reload callbacks
3. **Handler Updates**: LLM and TTS handlers automatically update their settings
4. **Model Reinitialization**: If model names change, handlers reinitialize automatically

## What Gets Reloaded

### ✅ Immediate Updates (No Restart Required)
- Generation parameters (temperature, max_tokens, top_p, etc.)
- Audio settings (volume, chunk_size, buffer_size)
- UI settings (auto_scroll, chat_history, etc.)
- WebSocket configuration (host, port, protocol)

### 🔄 Model Reinitialization (Brief Pause)
- LLM model name changes
- TTS model name changes
- TTS sample rate changes

### ❌ Requires Full Restart
- Server host/port changes (only for the server itself)
- Debug mode changes (affects uvicorn reload behavior)

## Usage Examples

### Testing Configuration Changes

1. **Start the application**:
   ```bash
   python backend/main.py
   ```

2. **Edit `.env` file** (while app is running):
   ```bash
   # Change generation temperature
   TEMPERATURE=0.9
   
   # Change max tokens
   MAX_NEW_TOKENS=256
   
   # Change audio settings
   TTS_SAMPLE_RATE=22050
   ```

3. **Watch the logs** - You'll see reload notifications instantly!

### Demo Script

Run the demonstration to see auto-reload in action:

```bash
python demo_config_reload.py
```

Then edit the `.env` file and watch changes appear in real-time.

### Test Script

Test with model handlers (without heavy model loading):

```bash
python test_auto_reload.py
```

## Technical Implementation

### Configuration Manager (`backend/utils/config_manager.py`)
- Centralized configuration management
- File watching with debouncing
- Callback system for notifications
- Thread-safe async handling

### Model Handler Updates
- LLM Handler: Automatic parameter updates + model reinitialization
- TTS Handler: Audio settings updates + model reinitialization
- Chat Handler: Inherits updates from LLM/TTS handlers

### Frontend Configuration
- Dynamic config endpoint (`/config`)
- Real-time updates for UI settings
- WebSocket URL reconfiguration

## Benefits

1. **🚀 Faster Development**: No need to restart during configuration changes
2. **🔧 Easy Tuning**: Adjust generation parameters in real-time
3. **🎛️ Live Audio Tweaking**: Change audio settings without interruption
4. **📊 A/B Testing**: Compare different model settings instantly
5. **🐛 Easier Debugging**: Test different configurations rapidly

## Dependencies

- `watchdog>=3.0.0` - File system monitoring
- `python-dotenv>=1.0.0` - Environment variable loading

## Logging

Watch for these log messages:
- `📝 .env file changed` - File modification detected
- `🔄 Configuration loaded` - Config reloaded from file
- `🔄 LLM config updated` - Model settings updated
- `🔄 TTS config updated` - Audio settings updated
- `🔄 Model changed, reinitializing` - Model reinitialization triggered

Enjoy seamless configuration management! 🎉
