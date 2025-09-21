"""
Voice Multi-Agent Bot with Azure AI Foundry Agent Mode (Solution B)

This implementation eliminates race conditions by using Azure AI Foundry agents 
directly through the Voice Live API instead of local orchestration.

Key Features:
- Direct Azure AI Foundry agent integration
- Eliminates race conditions between local and remote AI responses  
- Uses DefaultAzureCredential for secure authentication
- Professional conversation flow logging
- Voice-optimized multi-agent orchestration

Architecture:
- Voice Live API connects directly to Azure AI Foundry agents
- No local LLM processing (eliminates race conditions)
- Single source of truth for AI responses
- WebSocket-based real-time voice communication
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

# Load environment variables from current directory (.env)
load_dotenv()

# Configure professional logging with conversation flow tracking
setup_professional_logging(level="INFO")
logger = logging.getLogger(__name__)
flow_logger = ConversationFlowLogger(__name__)

# Initialize FastAPI application with comprehensive metadata
app = FastAPI(
    title="Voice Multi-Agent Bot - Azure AI Foundry Mode", 
    version="1.0.0",
    description="Voice-enabled multi-agent system using Azure AI Foundry for healthcare appointment preparation",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    Primary WebSocket endpoint for voice interaction using Azure AI Foundry Agent Mode.
    
    This endpoint provides real-time voice communication with Azure AI Foundry agents,
    eliminating race conditions by connecting directly to the Voice Live API.
    
    Features:
    - Real-time audio streaming via WebSocket
    - Direct Azure AI Foundry agent integration
    - Professional conversation flow logging
    - Automatic session management
    - Health check support (ping/pong)
    
    Message Types:
    - Binary: Raw audio data for voice processing
    - Text: JSON messages for ping/pong and control
    """
    await websocket.accept()
    
    # Generate unique session ID for conversation tracking
    session_id = str(uuid.uuid4())
    flow_logger.conversation_start(session_id, "voice_websocket_agent_mode")

    # Configuration for Azure AI Foundry Agent Mode
    # Note: Uses DefaultAzureCredential for authentication, API key as fallback
    config = {
        "AZURE_VOICE_LIVE_ENDPOINT": os.getenv("AZURE_VOICE_LIVE_ENDPOINT"),
        "AZURE_VOICE_LIVE_API_KEY": os.getenv("AZURE_VOICE_LIVE_API_KEY"),
        "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID": os.getenv("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        # Agent ID and project name are read directly by the handler
    }

    # Validate required Voice Live API configuration
    if not config["AZURE_VOICE_LIVE_ENDPOINT"]:
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": "AZURE_VOICE_LIVE_ENDPOINT not configured. Please set your Azure AI Foundry endpoint."
        }))
        return
        
    # Validate Azure AI Foundry Agent configuration
    if not os.getenv("AZURE_AI_FOUNDRY_AGENT_ID"):
        await websocket.send_text(json.dumps({
            "type": "error", 
            "text": "AZURE_AI_FOUNDRY_AGENT_ID not configured. Please set your Azure AI Foundry agent ID."
        }))
        return
        
    if not os.getenv("AI_FOUNDRY_PROJECT_NAME"):
        await websocket.send_text(json.dumps({
            "type": "error",
            "text": "AI_FOUNDRY_PROJECT_NAME not configured. Please set your Azure AI Foundry project name."
        }))
        return

    # Initialize Azure AI Foundry Agent Handler (eliminates race conditions)
    handler = VoiceLiveAgentHandler(config)
    
    try:
        # Establish client WebSocket connection for real-time audio streaming
        await handler.init_incoming_websocket(websocket, is_raw_audio=True)
        
        # Connect directly to Azure AI Foundry via Voice Live API
        # This eliminates race conditions by bypassing local orchestration
        await handler.connect()
        
        # Notify client that the voice agent is ready for interaction
        await websocket.send_text(json.dumps({
            "type": "ready", 
            "text": "Voice Multi-Agent Assistant connected to Azure AI Foundry!",
            "mode": "azure_ai_foundry_agent",
            "session_id": session_id
        }))
        
        # Log successful agent mode initialization
        flow_logger.agent_processing(session_id, "AzureAIFoundry", "agent_mode_initialized")
        
        # Main message processing loop - handles real-time voice communication
        while True:
            try:
                # Receive message from client (audio data or control messages)
                message = await websocket.receive()
                
                if message["type"] == "websocket.disconnect":
                    logger.info(f"Client disconnected - Session: {session_id}")
                    break
                    
                elif message["type"] == "websocket.receive":
                    # Handle text-based control messages (ping/pong, status)
                    if "text" in message:
                        try:
                            data = json.loads(message["text"])
                            
                            # Health check ping - ensure connection is active
                            if data.get("type") == "ping":
                                await websocket.send_text(json.dumps({
                                    "type": "pong",
                                    "text": "Voice Multi-Agent Assistant is ready",
                                    "mode": "azure_ai_foundry_agent",
                                    "session_id": session_id,
                                    "agent_id": os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")
                                }))
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in text message - Session: {session_id}")
                            
                    # Handle binary audio data - core voice processing
                    elif "bytes" in message:
                        audio_bytes = message["bytes"]
                        logger.debug(f"Processing audio data - Size: {len(audio_bytes)} bytes, Session: {session_id}")
                        
                        # Forward audio directly to Azure AI Foundry via Voice Live API
                        # This eliminates local processing and race conditions
                        await handler.web_to_voicelive(audio_bytes)
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during message processing - Session: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message in session {session_id}: {e}")
                # Continue processing other messages unless it's a critical error
                break

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from voice endpoint - Session: {session_id}")
    except Exception as e:
        logger.error(f"Voice WebSocket error in session {session_id}: {e}")
        try:
            # Attempt to send error message to client if connection is still active
            await websocket.send_text(json.dumps({
                "type": "error",
                "text": f"Voice agent connection error: {str(e)}",
                "session_id": session_id
            }))
        except:
            # Connection may already be closed
            pass
    finally:
        # Ensure proper cleanup of Voice Live API connection
        if 'handler' in locals():
            try:
                await handler.close()
                logger.info(f"Voice handler closed successfully - Session: {session_id}")
            except Exception as cleanup_error:
                logger.error(f"Error during handler cleanup - Session: {session_id}: {cleanup_error}")
        
        # Log conversation end for tracking
        flow_logger.conversation_start(session_id, "voice_websocket_agent_mode_ended")
        logger.info(f"Voice WebSocket connection closed (Agent Mode) - Session: {session_id}")


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