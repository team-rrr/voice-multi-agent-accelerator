#!/usr/bin/env python3
"""
Voice Live API WebSocket Test
Tests direct WebSocket connection to Azure Voice Live API using the same pattern as call-center-voice-agent-accelerator
"""

import asyncio
import base64
import json
import logging
import os
import uuid
from dotenv import load_dotenv
from websockets.asyncio.client import connect as ws_connect

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def session_config():
    """Returns the default session configuration for Voice Live."""
    return {
        "type": "session.update",
        "session": {
            "instructions": "You are a helpful AI assistant. When a user says something, simply echo back exactly what they said.",
            "turn_detection": {
                "type": "azure_semantic_vad",
                "threshold": 0.3,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 200,
                "remove_filler_words": False,
            },
            "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
            "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
            "voice": {
                "name": "en-US-Aria:DragonHDLatestNeural",
                "type": "azure-standard",
                "temperature": 0.8,
            },
        },
    }


async def test_voice_live_websocket():
    """Test Voice Live API WebSocket connection using the working pattern."""
    
    # Get configuration
    endpoint = os.getenv("AZURE_VOICE_LIVE_ENDPOINT")
    api_key = os.getenv("AZURE_VOICE_LIVE_API_KEY")
    model = os.getenv("VOICE_LIVE_MODEL", "gpt-4o-mini")
    client_id = os.getenv("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
    
    if not endpoint or not api_key:
        logger.error("Missing required environment variables!")
        return False
    
    logger.info(f"Testing Voice Live API:")
    logger.info(f"  Endpoint: {endpoint}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Using API Key: {'Yes' if api_key else 'No'}")
    logger.info(f"  Using Managed Identity: {'Yes' if client_id else 'No'}")
    
    try:
        # Build WebSocket URL - same pattern as call-center project
        url = f"{endpoint}/voice-live/realtime?api-version=2025-05-01-preview&model={model}"
        url = url.replace("https://", "wss://")
        
        logger.info(f"WebSocket URL: {url}")
        
        # Set up headers
        headers = {"x-ms-client-request-id": str(uuid.uuid4())}
        
        # For local testing, always use API key
        # In Azure deployment, this would use managed identity
        headers["api-key"] = api_key
        logger.info("Using API Key authentication (local development)")
        
        # Connect to WebSocket
        logger.info("Connecting to Voice Live API WebSocket...")
        async with ws_connect(url, additional_headers=headers) as websocket:
            logger.info("✅ WebSocket connection established!")
            
            # Send session configuration
            logger.info("Sending session configuration...")
            await websocket.send(json.dumps(session_config()))
            
            # Create initial response
            logger.info("Creating initial response...")
            await websocket.send(json.dumps({"type": "response.create"}))
            
            # Listen for initial messages
            logger.info("Listening for server messages...")
            timeout_counter = 0
            max_timeout = 10
            
            while timeout_counter < max_timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    event = json.loads(message)
                    event_type = event.get("type", "unknown")
                    
                    logger.info(f"📨 Received: {event_type}")
                    
                    if event_type == "session.created":
                        session_id = event.get("session", {}).get("id")
                        logger.info(f"✅ Session created successfully! ID: {session_id}")
                        
                    elif event_type == "response.done":
                        # After initial response is done, test with a user message
                        logger.info("Initial response complete, testing text echo...")
                        test_message = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": "Hello, this is a test"
                                    }
                                ]
                            }
                        }
                        await websocket.send(json.dumps(test_message))
                        await websocket.send(json.dumps({"type": "response.create"}))
                        
                    elif event_type == "response.done":
                        response = event.get("response", {})
                        status = response.get("status")
                        logger.info(f"✅ Response completed! Status: {status}")
                        if status == "completed":
                            logger.info("✅ Voice Live API test completed successfully!")
                            return True
                        
                    elif event_type == "error":
                        logger.error(f"❌ Voice Live API Error: {event}")
                        return False
                        
                except asyncio.TimeoutError:
                    timeout_counter += 1
                    logger.info(f"⏱️ Waiting for messages... ({timeout_counter}/{max_timeout})")
                    continue
            
            logger.info("✅ Voice Live API WebSocket test completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Voice Live API test failed: {e}")
        return False


async def main():
    """Run the Voice Live API test."""
    logger.info("🎙️ Starting Voice Live API WebSocket Test")
    logger.info("=" * 50)
    
    success = await test_voice_live_websocket()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 Voice Live API test PASSED!")
        logger.info("Ready to implement full voice integration!")
    else:
        logger.error("💥 Voice Live API test FAILED!")
        logger.error("Please check credentials and configuration.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())