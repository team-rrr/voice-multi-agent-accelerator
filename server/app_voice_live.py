"""
Voice Multi-Agent Echo Bot with Voice Live API Integration
Full implementation using Azure Voice Live API for real-time voice processing
"""

import os
import logging
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from voice_live_handler import VoiceLiveHandler

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Multi-Agent Echo Bot", version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice interaction using Voice Live API."""
    await websocket.accept()
    logger.info("Voice WebSocket connection accepted")

    # Get configuration
    config = {
        "AZURE_VOICE_LIVE_ENDPOINT": os.getenv("AZURE_VOICE_LIVE_ENDPOINT"),
        "AZURE_VOICE_LIVE_API_KEY": os.getenv("AZURE_VOICE_LIVE_API_KEY"),
        "VOICE_LIVE_MODEL": os.getenv("VOICE_LIVE_MODEL", "gpt-4o-mini"),
        "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID": os.getenv("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
    }

    # Validate configuration
    if not config["AZURE_VOICE_LIVE_ENDPOINT"] or not config["AZURE_VOICE_LIVE_API_KEY"]:
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": "Voice Live API credentials not configured"
        }))
        return

    # Initialize Voice Live handler
    handler = VoiceLiveHandler(config)
    
    try:
        # Set up client WebSocket connection
        await handler.init_incoming_websocket(websocket, is_raw_audio=True)
        
        # Connect to Voice Live API
        await handler.connect()
        
        # Send ready message to client
        await websocket.send_text(json.dumps({
            "type": "ready",
            "text": "Voice Live Echo Bot is ready! You can speak or send text messages."
        }))
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                message = await websocket.receive()
                
                if message["type"] == "websocket.receive":
                    # Handle different message types
                    if "text" in message:
                        # Text message
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "text":
                            # Send text to Voice Live for processing
                            text = data.get("text", "")
                            logger.info(f"Received text from client: {text}")
                            await handler.text_to_voicelive(text)
                            
                        elif data.get("type") == "ping":
                            # Respond to ping
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "text": "Echo Bot is alive"
                            }))
                            
                    elif "bytes" in message:
                        # Binary audio data
                        audio_bytes = message["bytes"]
                        logger.debug(f"Received {len(audio_bytes)} bytes of audio data")
                        await handler.web_to_voicelive(audio_bytes)
                        
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                break

    except WebSocketDisconnect:
        logger.info("Client disconnected from voice endpoint")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": f"Voice Live API error: {str(e)}"
        }))
    finally:
        # Clean up handler
        if 'handler' in locals():
            await handler.close()
        logger.info("Voice WebSocket connection closed")


@app.websocket("/ws/text")
async def websocket_text_endpoint(websocket: WebSocket):
    """WebSocket endpoint for text-only echo (fallback/testing)."""
    await websocket.accept()
    logger.info("Text WebSocket connection accepted")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"Received text message: {data}")
            
            try:
                # Try to parse as JSON
                message = json.loads(data)
                if message.get("type") == "text":
                    # Echo back the text
                    response = {
                        "type": "echo",
                        "text": f"Echo: {message.get('text', '')}"
                    }
                    await websocket.send_text(json.dumps(response))
                    logger.info(f"Echoed: {response}")
            except json.JSONDecodeError:
                # If not JSON, just echo the raw text
                response = {
                    "type": "echo", 
                    "text": f"Echo: {data}"
                }
                await websocket.send_text(json.dumps(response))
                logger.info(f"Echoed raw text: {response}")

    except WebSocketDisconnect:
        logger.info("Client disconnected from text endpoint")
    except Exception as e:
        logger.error(f"Text WebSocket error: {e}")
    finally:
        logger.info("Text WebSocket connection closed")


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "Voice Multi-Agent Echo Bot", 
        "status": "running",
        "version": "0.1.0",
        "endpoints": {
            "voice_websocket": "/ws/voice",
            "text_websocket": "/ws/text", 
            "health": "/health",
            "static_files": "/static/"
        },
        "description": "Real-time voice echo bot using Azure Voice Live API"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "voice_live_endpoint_configured": bool(os.getenv("AZURE_VOICE_LIVE_ENDPOINT")),
        "voice_live_key_configured": bool(os.getenv("AZURE_VOICE_LIVE_API_KEY")),
        "voice_live_model": os.getenv("VOICE_LIVE_MODEL", "gpt-4o-mini"),
        "acs_connection_configured": bool(os.getenv("ACS_CONNECTION_STRING"))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)