"""
FastAPI backend for SpeakStream - Real-time streaming chatbot
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

from models.llm_handler import LLMHandler
from models.tts_handler import TTSHandler
from websocket.chat_handler import ChatHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global handlers
llm_handler = None
tts_handler = None
chat_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app"""
    global llm_handler, tts_handler, chat_handler
    
    # Startup
    logger.info("🚀 Starting SpeakStream backend...")
    
    # Initialize LLM handler
    logger.info("📚 Loading SmolLM2-135M-Instruct model...")
    llm_handler = LLMHandler()
    await llm_handler.initialize()
    
    # Initialize TTS handler
    logger.info("🔊 Loading Coqui TTS model...")
    tts_handler = TTSHandler()
    await tts_handler.initialize()
    
    # Initialize chat handler
    chat_handler = ChatHandler(llm_handler, tts_handler)
    
    logger.info("✅ All models loaded successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SpeakStream backend...")

# Initialize FastAPI app with lifespan
app = FastAPI(title="SpeakStream", version="1.0.0", lifespan=lifespan)

# WebSocket endpoint for chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat communication"""
    await websocket.accept()
    logger.info("🔌 New WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"📨 Received message: {data[:50]}...")
            
            # Process the message through chat handler
            await chat_handler.handle_message(websocket, data)
            
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket connection closed")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await websocket.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_loaded": llm_handler is not None,
        "tts_loaded": tts_handler is not None
    }

# Serve static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    # Mount CSS files
    css_path = frontend_path / "css"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    
    # Mount JS files
    js_path = frontend_path / "js"
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    
    # Mount entire frontend as fallback
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Root endpoint to serve the frontend
@app.get("/")
async def get_frontend():
    """Serve the main frontend page"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        with open(frontend_file, 'r') as f:
            return HTMLResponse(content=f.read())
    return {"message": "SpeakStream API is running! Frontend not found."}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
