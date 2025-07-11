#!/usr/bin/env python3
"""
Simple WebSocket client to test the SpeakStream backend
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a test message
            test_message = {
                "type": "chat",
                "message": "Hello test"
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent: {test_message}")
            
            # Listen for responses
            response_count = 0
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")
                    
                    print(f"📨 Received {message_type}: {str(data)[:200]}...")
                    
                    if message_type == "chunk":
                        chunk_data = data.get("data", {})
                        chunk_type = chunk_data.get("type", "unknown")
                        print(f"   📦 Chunk type: {chunk_type}")
                        
                        if chunk_type == "audio":
                            audio_data = chunk_data.get("data", "")
                            print(f"   🔊 Audio chunk {chunk_data.get('chunk_id')}: {len(audio_data)} bytes")
                    
                    response_count += 1
                    if response_count > 20:  # Limit responses
                        print("⏹️ Stopping after 20 responses")
                        break
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {message}")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
