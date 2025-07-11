"""
Development configuration and utilities
"""
import os
import sys
import logging
from pathlib import Path

def setup_development_environment():
    """Setup development environment"""
    # Add backend to Python path
    backend_path = Path(__file__).parent / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Environment variables
    os.environ.setdefault('TORCH_HOME', './models/torch_cache')
    os.environ.setdefault('HF_HOME', './models/hf_cache')
    os.environ.setdefault('TRANSFORMERS_CACHE', './models/transformers_cache')
    
    print("✅ Development environment configured")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'websockets',
        'torch',
        'transformers',
        'TTS',
        'soundfile',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are installed")
        return True

def download_models():
    """Download required models if not present"""
    print("📥 Checking/downloading models...")
    
    try:
        # Test SmolLM2 model
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-135M-Instruct")
        print("✅ SmolLM2-135M-Instruct tokenizer ready")
        
        # Test TTS model (will download on first use)
        from TTS.api import TTS
        tts = TTS("tts_models/en/ljspeech/glow-tts")
        print("✅ Coqui TTS glow-tts model ready")
        
    except Exception as e:
        print(f"⚠️ Model download issue: {e}")
        print("💡 Models will be downloaded on first use")

if __name__ == "__main__":
    setup_development_environment()
    
    if check_dependencies():
        download_models()
        print("🎉 Setup complete! Run: python backend/main.py")
    else:
        print("❌ Setup incomplete - please install missing dependencies")
