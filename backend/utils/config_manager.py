"""
Configuration Manager with auto-reload functionality
Watches .env file for changes and updates configuration dynamically
"""
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration with auto-reload functionality"""
    
    def __init__(self, env_file_path: Optional[str] = None):
        self.env_file_path = env_file_path or self._find_env_file()
        self.config = {}
        self.observers = []
        self.file_observer = None
        self.reload_callbacks = []
        self.last_modified = 0
        
        # Load initial configuration
        self.load_config()
        
    def _find_env_file(self) -> str:
        """Find the .env file in the project root"""
        current_dir = Path(__file__).parent
        while current_dir != current_dir.parent:
            env_file = current_dir / ".env"
            if env_file.exists():
                return str(env_file)
            current_dir = current_dir.parent
        
        # Default to current working directory
        return os.path.join(os.getcwd(), ".env")
    
    def load_config(self):
        """Load configuration from .env file"""
        try:
            # Reload environment variables
            load_dotenv(self.env_file_path, override=True)
            
            # Update internal config cache
            self.config = {
                # Server Settings
                "HOST": os.getenv("HOST", "0.0.0.0"),
                "PORT": int(os.getenv("PORT", "8000")),
                "DEBUG": os.getenv("DEBUG", "true").lower() == "true",
                
                # Model Settings
                "LLM_MODEL_NAME": os.getenv("LLM_MODEL_NAME", "HuggingFaceTB/SmolLM2-135M-Instruct"),
                "TTS_MODEL_NAME": os.getenv("TTS_MODEL_NAME", "tts_models/en/ljspeech/glow-tts"),
                "TTS_SAMPLE_RATE": int(os.getenv("TTS_SAMPLE_RATE", "22050")),
                "TTS_SPEAKER": os.getenv("TTS_SPEAKER", None),
                
                # WebSocket Settings
                "WS_HOST": os.getenv("WS_HOST", "localhost"),
                "WS_PORT": int(os.getenv("WS_PORT", os.getenv("PORT", "8000"))),
                "WS_PROTOCOL": os.getenv("WS_PROTOCOL", "ws"),
                
                # Audio Settings
                "DEFAULT_VOLUME": float(os.getenv("DEFAULT_VOLUME", "0.8")),
                "CHUNK_SIZE": int(os.getenv("CHUNK_SIZE", "1024")),
                "MAX_QUEUE_SIZE": int(os.getenv("MAX_QUEUE_SIZE", "10")),
                
                # Generation Settings
                "MAX_NEW_TOKENS": int(os.getenv("MAX_NEW_TOKENS", "512")),
                "TEMPERATURE": float(os.getenv("TEMPERATURE", "0.7")),
                "TOP_P": float(os.getenv("TOP_P", "0.9")),
                "DO_SAMPLE": os.getenv("DO_SAMPLE", "true").lower() == "true",
                
                # UI Settings
                "AUTO_SCROLL": os.getenv("AUTO_SCROLL", "true").lower() == "true",
                "SAVE_CHAT_HISTORY": os.getenv("SAVE_CHAT_HISTORY", "true").lower() == "true",
                "MAX_CHAT_HISTORY": int(os.getenv("MAX_CHAT_HISTORY", "100")),
                
                # Performance Settings
                "ENABLE_AUDIO": os.getenv("ENABLE_AUDIO", "true").lower() == "true",
                "AUDIO_BUFFER_SIZE": int(os.getenv("AUDIO_BUFFER_SIZE", "8192")),
            }
            
            logger.info(f"🔄 Configuration loaded from {self.env_file_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()
    
    def add_reload_callback(self, callback: Callable):
        """Add a callback to be called when configuration is reloaded"""
        self.reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable):
        """Remove a reload callback"""
        if callback in self.reload_callbacks:
            self.reload_callbacks.remove(callback)
    
    async def notify_reload(self):
        """Notify all callbacks about configuration reload"""
        logger.info("🔄 Notifying handlers about configuration reload...")
        
        for callback in self.reload_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.config)
                else:
                    callback(self.config)
            except Exception as e:
                logger.error(f"❌ Error in reload callback: {e}")
    
    def start_watching(self):
        """Start watching the .env file for changes"""
        if self.file_observer is not None:
            return  # Already watching
        
        class EnvFileHandler(FileSystemEventHandler):
            def __init__(self, config_manager):
                self.config_manager = config_manager
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                if event.src_path == self.config_manager.env_file_path:
                    current_time = time.time()
                    # Debounce rapid file changes (some editors save multiple times)
                    if current_time - self.config_manager.last_modified > 1:
                        self.config_manager.last_modified = current_time
                        logger.info(f"📝 .env file changed: {event.src_path}")
                        
                        # Reload configuration
                        self.config_manager.load_config()
                        
                        # Schedule async notification in a thread-safe way
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(self.config_manager.notify_reload())
                        except RuntimeError:
                            # No event loop running, schedule for later
                            import threading
                            def delayed_notify():
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(self.config_manager.notify_reload())
                                    loop.close()
                                except Exception as e:
                                    logger.error(f"❌ Error in delayed notification: {e}")
                            
                            thread = threading.Thread(target=delayed_notify)
                            thread.daemon = True
                            thread.start()
        
        # Set up file watcher
        event_handler = EnvFileHandler(self)
        self.file_observer = Observer()
        
        # Watch the directory containing the .env file
        watch_dir = os.path.dirname(self.env_file_path)
        self.file_observer.schedule(event_handler, watch_dir, recursive=False)
        self.file_observer.start()
        
        logger.info(f"👁️ Started watching {self.env_file_path} for changes")
    
    def stop_watching(self):
        """Stop watching the .env file"""
        if self.file_observer is not None:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None
            logger.info("🛑 Stopped watching .env file")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_watching()

# Global configuration manager instance
config_manager = ConfigManager()
