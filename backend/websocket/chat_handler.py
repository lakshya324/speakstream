"""
WebSocket chat handler that coordinates LLM and TTS
"""
import asyncio
import json
import logging
from fastapi import WebSocket
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ChatHandler:
    """Handles WebSocket chat communication and coordinates LLM + TTS"""
    
    def __init__(self, llm_handler, tts_handler):
        self.llm_handler = llm_handler
        self.tts_handler = tts_handler
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming chat message"""
        try:
            # Parse the incoming message
            data = json.loads(message)
            message_type = data.get("type", "chat")
            user_message = data.get("message", "")
            
            logger.info(f"📨 Processing {message_type} message: {user_message[:50]}...")
            
            if message_type == "chat":
                await self._handle_chat_message(websocket, user_message)
            elif message_type == "ping":
                await self._handle_ping(websocket)
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            await self._send_error(websocket, f"Server error: {str(e)}")
    
    async def _handle_chat_message(self, websocket: WebSocket, user_message: str):
        """Handle chat message with streaming response"""
        if not user_message.strip():
            await self._send_error(websocket, "Empty message")
            return
        
        try:
            # Send acknowledgment
            await self._send_message(websocket, {
                "type": "response_start",
                "message": "Generating response..."
            })
            
            # Generate streaming text from LLM
            text_stream = self.llm_handler.generate_stream(user_message)
            
            # Process text stream through TTS
            audio_stream = self.tts_handler.synthesize_stream(text_stream)
            
            # Stream responses to client
            response_chunks = []
            async for chunk in audio_stream:
                # Send chunk to client in the expected format
                await self._send_message(websocket, {
                    "type": "chunk",
                    "data": chunk
                })
                
                # Keep track of text chunks for final response
                if chunk.get("type") == "text":
                    response_chunks.append(chunk.get("data", ""))
            
            # Send completion signal
            full_response = "".join(response_chunks)
            await self._send_message(websocket, {
                "type": "response_complete",
                "full_text": full_response,
                "message": "Response generation completed"
            })
            
            logger.info(f"✅ Completed response generation for: {user_message[:30]}...")
            
        except Exception as e:
            logger.error(f"❌ Error in chat response: {e}")
            await self._send_error(websocket, f"Failed to generate response: {str(e)}")
    
    async def _handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await self._send_message(websocket, {
            "type": "pong",
            "message": "Server is alive"
        })
    
    async def _send_message(self, websocket: WebSocket, data: dict):
        """Send message to websocket client"""
        try:
            message = json.dumps(data)
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to client"""
        await self._send_message(websocket, {
            "type": "error",
            "message": error_message
        })
    
    async def connect(self, websocket: WebSocket):
        """Register new websocket connection"""
        self.active_connections[websocket] = {
            "connected_at": asyncio.get_event_loop().time(),
            "message_count": 0
        }
        logger.info(f"🔌 New connection registered. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Unregister websocket connection"""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logger.info(f"🔌 Connection removed. Total: {len(self.active_connections)}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
