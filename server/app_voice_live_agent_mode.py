"""
Solution B: Voice Multi-Agent Bot with Azure AI Foundry Agent Mode
Eliminates race condition by using Azure AI Foundry a    finally:
        # Clean up handler
        if 'handler' in locals()    finally:
        logger.info(f"Text WebSocket connection closed - Session: {session_id}")            await handler.close()
        logger.info(f"Voice WebSocket connection closed (Agent Mode) - Session: {session_id}")instead of local orchestration
"""

import os
import logging
import json
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
from voice_live_agent_handler_agent_mode import VoiceLiveAgentHandler  # Solution B Azure AI Foundry Agent Mode handler
from logging_config import ConversationFlowLogger, setup_professional_logging

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Configure professional logging
setup_professional_logging(level="INFO")
logger = logging.getLogger(__name__)
flow_logger = ConversationFlowLogger(__name__)

app = FastAPI(title="Voice Multi-Agent Bot - Azure AI Foundry Mode", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice interaction using Azure AI Foundry Agent Mode (Solution B)."""
    await websocket.accept()
    
    # Generate unique session ID for this WebSocket connection
    session_id = str(uuid.uuid4())
    flow_logger.conversation_start(session_id, "voice_websocket_agent_mode")

    # Get configuration for Azure AI Foundry Agent Mode (simplified)
    config = {
        "AZURE_VOICE_LIVE_ENDPOINT": os.getenv("AZURE_VOICE_LIVE_ENDPOINT"),
        "AZURE_VOICE_LIVE_API_KEY": os.getenv("AZURE_VOICE_LIVE_API_KEY"),
        "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID": os.getenv("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        # Note: AZURE_AI_FOUNDRY_AGENT_ID is read directly from environment in handler
    }

    # Validate configuration
    if not config["AZURE_VOICE_LIVE_ENDPOINT"] or not config["AZURE_VOICE_LIVE_API_KEY"]:
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": "Voice Live API credentials not configured"
        }))
        return
        
    # Check if Azure AI Foundry Agent ID is configured
    if not os.getenv("AZURE_AI_FOUNDRY_AGENT_ID"):
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": "AZURE_AI_FOUNDRY_AGENT_ID not configured"
        }))
        return

    # Initialize Solution B: Voice Live Agent Handler (eliminates race condition)
    handler = VoiceLiveAgentHandler(config)
    
    try:
        # Set up client WebSocket connection
        await handler.init_incoming_websocket(websocket, is_raw_audio=True)
        
        # Connect to Voice Live API in Agent Mode
        await handler.connect()
        
        # Send ready message to client
        await websocket.send_text(json.dumps({
            "type": "ready", 
            "text": "Voice Multi-Agent Assistant is ready!"
        }))
        
        flow_logger.agent_processing(session_id, "AzureAIFoundry", "agent_mode_initialized")
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                message = await websocket.receive()
                
                if message["type"] == "websocket.disconnect":
                    logger.info("Client initiated WebSocket disconnect")
                    break
                elif message["type"] == "websocket.receive":
                    # Handle different message types
                    if "text" in message:
                        # Handle ping messages for connection health checks
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "ping":
                            # Respond to ping
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "text": "Voice Multi-Agent Assistant is ready",
                                "mode": "azure_ai_foundry_agent"
                            }))
                            
                    elif "bytes" in message:
                        # Binary audio data - forward to Azure AI Foundry agents
                        audio_bytes = message["bytes"]
                        logger.debug(f"Audio data received - Size: {len(audio_bytes)} bytes")
                        await handler.web_to_voicelive(audio_bytes)
                        
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                break

    except WebSocketDisconnect:
        logger.info("Client disconnected from voice endpoint")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": f"Voice Live Agent Mode error: {str(e)}"
        }))
    finally:
        # Clean up handler
        if 'handler' in locals():
            await handler.close()
        flow_logger.conversation_start(session_id, "voice_websocket_agent_mode_ended")
        logger.info("Voice WebSocket connection closed (Agent Mode)")


@app.websocket("/ws/text")
async def websocket_text_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for text-only interaction (legacy mode).
    Note: This endpoint is maintained for testing but Azure AI Foundry agents 
    are primarily designed for voice interaction through the Voice Live API.
    """
    await websocket.accept()
    
    # Generate unique session ID for this WebSocket connection
    session_id = str(uuid.uuid4())
    flow_logger.conversation_start(session_id, "text_websocket_legacy")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            flow_logger.user_message(session_id, data, "text")
            
            try:
                # Try to parse as JSON
                message = json.loads(data)
                if message.get("type") == "text":
                    # In Solution B, text interaction would need to call Azure AI Foundry directly
                    # For now, provide informative response
                    user_text = message.get('text', '')
                    if user_text.strip():
                        response = {
                            "type": "info",
                            "text": f"Text received: '{user_text}'. For full multi-agent experience, please use voice interaction. Azure AI Foundry agents are optimized for voice workflows.",
                            "suggestion": "Switch to voice mode for complete multi-agent orchestration"
                        }
                        await websocket.send_text(json.dumps(response))
                    else:
                        response = {
                            "type": "prompt",
                            "text": "Voice Multi-Agent Assistant (Azure AI Foundry Mode). For best experience, use voice interaction."
                        }
                        await websocket.send_text(json.dumps(response))
                        
                elif message.get("type") == "ping":
                    # Health check ping
                    response = {
                        "type": "pong",
                        "text": "Multi-Agent Assistant is alive (Azure AI Foundry Mode)",
                        "mode": "azure_ai_foundry_agent",
                        "session_id": session_id
                    }
                    await websocket.send_text(json.dumps(response))
                    
            except json.JSONDecodeError:
                # If not JSON, provide info about agent mode
                response = {
                    "type": "info",
                    "text": f"Input received: '{data[:100]}'. This system now uses Azure AI Foundry agents for voice interaction. Please use the voice interface for full functionality."
                }
                await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        logger.info("Client disconnected from text endpoint")
    except Exception as e:
        logger.error(f"Text WebSocket error: {e}")
    finally:
        flow_logger.conversation_start(session_id, "text_websocket_legacy_ended")
        logger.info("Text WebSocket connection closed")


@app.get("/")
def read_root():
    """Root endpoint with API information for Solution B."""
    return {
        "message": "Voice Multi-Agent Assistant - Azure AI Foundry Mode", 
        "status": "running",
        "version": "1.0.0 - Solution B",
        "mode": "azure_ai_foundry_agent",
        "race_condition_status": "eliminated",
        "endpoints": {
            "voice_websocket": "/ws/voice",
            "text_websocket": "/ws/text", 
            "health": "/health",
            "api_query": "/api/query",
            "static_files": "/static/"
        },
        "description": "Voice multi-agent assistant using Azure AI Foundry Agent Mode to eliminate race conditions",
        "features": [
            "Azure AI Foundry multi-agent orchestration",
            "Voice Live API agent mode (eliminates race condition)",
            "Professional conversation flow logging",
            "Single AI response system"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint for Solution B."""
    return {
        "status": "healthy",
        "mode": "azure_ai_foundry_agent",
        "voice_live_endpoint_configured": bool(os.getenv("AZURE_VOICE_LIVE_ENDPOINT")),
        "voice_live_key_configured": bool(os.getenv("AZURE_VOICE_LIVE_API_KEY")),
        "agent_id_configured": bool(os.getenv("VOICE_LIVE_AGENT_ID")),
        "orchestrator_agent": os.getenv("AZURE_AI_ORCHESTRATOR_AGENT_ID", "not_configured"),
        "foundry_endpoint": os.getenv("AZURE_AI_FOUNDRY_ENDPOINT", "not_configured"),
        "race_condition_status": "eliminated_by_agent_mode",
        "acs_connection_configured": bool(os.getenv("ACS_CONNECTION_STRING")),
        "capabilities": [
            "Azure AI Foundry agent orchestration",
            "Single AI response (no race condition)",
            "Voice Live API agent mode integration",
            "Professional logging and debugging"
        ]
    }


class QueryRequest(BaseModel):
    text: str
    session_id: str = None  # Optional session_id


class AgentResponse(BaseModel):
    """Response model for Azure AI Foundry agent interactions."""
    text: str
    session_id: str
    agent_mode: str = "azure_ai_foundry"


@app.post("/api/query", response_model=AgentResponse)
async def http_query(request: QueryRequest):
    """
    Provides a text-based endpoint that demonstrates Azure AI Foundry integration.
    Note: For full multi-agent experience, use voice WebSocket endpoint.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"Received API query for Azure AI Foundry agents (session {session_id}): {request.text}")
    
    # In Solution B, this would make direct calls to Azure AI Foundry
    # For now, provide informative response about the agent mode
    response_text = f"Azure AI Foundry Agent Mode active. Query received: '{request.text}'. For full multi-agent orchestration, please use the voice WebSocket endpoint which connects directly to your deployed agents."
    
    return AgentResponse(
        text=response_text,
        session_id=session_id,
        agent_mode="azure_ai_foundry"
    )


@app.get("/api/agents")
def get_agent_status():
    """Debug endpoint to show Azure AI Foundry agent configuration."""
    return {
        "agent_mode": "azure_ai_foundry",
        "orchestrator_agent_id": os.getenv("AZURE_AI_ORCHESTRATOR_AGENT_ID", "not_configured"),
        "info_agent_id": os.getenv("AZURE_AI_INFO_AGENT_ID", "not_configured"),
        "patient_context_agent_id": os.getenv("AZURE_AI_PATIENT_CONTEXT_AGENT_ID", "not_configured"),
        "action_agent_id": os.getenv("AZURE_AI_ACTION_AGENT_ID", "not_configured"),
        "foundry_endpoint": os.getenv("AZURE_AI_FOUNDRY_ENDPOINT", "not_configured"),
        "voice_live_agent_id": os.getenv("VOICE_LIVE_AGENT_ID", "not_configured"),
        "race_condition_status": "eliminated",
        "deployment_phase": "solution_b_implemented"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)