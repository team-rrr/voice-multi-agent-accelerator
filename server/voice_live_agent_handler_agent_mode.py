"""
Azure AI Foundry Agent Mode Handler

This module provides a WebSocket handler that connects directly to Azure AI Foundry agents
through the Voice Live API, eliminating race conditions caused by local orchestration.

Key Features:
- Direct Azure AI Foundry agent integration via Voice Live API
- Eliminates race conditions between local and remote AI responses
- Real-time bidirectional audio streaming
- Azure DefaultAzureCredential authentication with API key fallback
- Professional conversation flow logging

Architecture:
- Client WebSocket ←→ VoiceLiveAgentHandler ←→ Azure Voice Live API ←→ Azure AI Foundry Agent
- Single source of AI responses (no local processing)
- Preserves multi-agent orchestration defined in Azure AI Foundry

Classes:
    VoiceLiveAgentHandler: Main handler for Azure AI Foundry agent connections

Functions:
    session_config(): Session configuration for model-based fallback mode
    agent_session_config(): Session configuration for Azure AI Foundry agent mode
"""

import asyncio
import base64
import json
import logging
import uuid
import os
from typing import Optional

from azure.identity import DefaultAzureCredential
from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Data
from logging_config import ConversationFlowLogger, setup_professional_logging

# Set up professional logging
setup_professional_logging(level="INFO")
logger = logging.getLogger(__name__)
flow_logger = ConversationFlowLogger(__name__)


def session_config():
    """
    Session configuration for model-based fallback mode.
    
    This configuration is used when falling back to direct model interaction
    instead of Azure AI Foundry agent mode. Includes custom instructions
    that simulate the multi-agent behavior.
    
    Returns:
        dict: Session configuration with instructions, audio settings, and voice parameters
    """
    config = {
        "type": "session.update",
        "session": {
            "instructions": "You are connected to an Azure AI Foundry multi-agent system for healthcare appointment preparation. Follow the agent orchestration exactly as configured.",
            "input_audio_sampling_rate": 24000,
            "turn_detection": {
                "type": "azure_semantic_vad",
                "threshold": 0.3,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 200,
                "remove_filler_words": False,
                "end_of_utterance_detection": {
                    "model": "semantic_detection_v1",
                    "threshold": 0.01,
                    "timeout": 2,
                },
            },
            "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
            "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
            "voice": {
                "name": "en-US-Ava:DragonHDLatestNeural",
                "type": "azure-standard",
                "temperature": 0.8,
            },
            "input_audio_transcription": {"model": "whisper-1"},
        },
    }
    
    logger.info(f"Session configuration prepared for Azure AI Foundry Agent Mode")
    return config

def agent_session_config():
    """
    Session configuration for Azure AI Foundry Agent Mode.
    
    This configuration is used for direct agent connections where instructions
    are pre-configured in the Azure AI Foundry agent and cannot be modified.
    Uses simplified audio processing parameters that are compatible with agent mode.
    
    Key differences from model mode:
    - No instructions (read-only in agent mode)
    - Simplified turn detection (server_vad instead of azure_semantic_vad)  
    - Standard transcription model (whisper-1)
    - Voice configured for US English (en-US-Ava:DragonHDLatestNeural)
    
    Returns:
        dict: Session configuration optimized for Azure AI Foundry agent mode
    """
    config = {
        "type": "session.update",
        "session": {
            # NOTE: No instructions in agent mode - they're pre-configured in Azure AI Foundry
            "input_audio_sampling_rate": 24000,
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 200
            },
            "voice": {
                "name": "en-US-Ava:DragonHDLatestNeural",
                "type": "azure-standard",
                "temperature": 0.8,
            },
            "input_audio_transcription": {"model": "whisper-1"},
        },
    }
    
    logger.info(f"Agent session configuration prepared for Azure AI Foundry Agent Mode (no instructions)")
    return config


class VoiceLiveAgentHandler:
    """
    Azure AI Foundry Agent Mode WebSocket Handler
    
    This handler provides a bridge between client WebSocket connections and Azure AI Foundry
    agents via the Voice Live API. It eliminates race conditions by bypassing local 
    orchestration and connecting directly to pre-configured agents.
    
    Architecture Flow:
    1. Client sends audio → VoiceLiveAgentHandler → Voice Live API → Azure AI Foundry Agent
    2. Azure AI Foundry Agent → Voice Live API → VoiceLiveAgentHandler → Client receives audio
    
    Key Features:
    - Eliminates race conditions (no local AI processing)
    - Real-time bidirectional audio streaming
    - Azure DefaultAzureCredential authentication with fallback
    - Automatic session management and error recovery
    - Professional conversation flow logging
    
    Attributes:
        endpoint (str): Azure Voice Live API endpoint
        api_key (str): API key for fallback authentication
        agent_id (str): Azure AI Foundry agent identifier
        project_name (str): Azure AI Foundry project name
        ws: WebSocket connection to Voice Live API
        send_queue: Async queue for message sending
        incoming_websocket: Client WebSocket connection
    """

    def __init__(self, config):
        """
        Initialize the Azure AI Foundry Agent Handler.
        
        Args:
            config (dict): Configuration dictionary containing:
                - AZURE_VOICE_LIVE_ENDPOINT: Voice Live API endpoint URL
                - AZURE_VOICE_LIVE_API_KEY: API key for fallback authentication
                - AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID: Optional managed identity client ID
        
        Raises:
            ValueError: If required agent configuration is missing
        """
        # Voice Live API Configuration
        self.endpoint = config["AZURE_VOICE_LIVE_ENDPOINT"]
        self.api_key = config.get("AZURE_VOICE_LIVE_API_KEY")  # Fallback authentication
        self.client_id = config.get("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        
        # Azure AI Foundry Agent Configuration
        # These are loaded from environment variables for security
        self.agent_id = os.getenv("AI_FOUNDRY_AGENT_ID")
        self.project_name = os.getenv("AI_FOUNDRY_PROJECT_NAME")
        
        # Validate required Azure AI Foundry configuration
        if not self.agent_id:
            logger.error("AI_FOUNDRY_AGENT_ID is not configured in environment variables")
            raise ValueError("AI_FOUNDRY_AGENT_ID is required for Agent Mode")
        if not self.project_name:
            logger.error("AI_FOUNDRY_PROJECT_NAME is not configured in environment variables")
            raise ValueError("AI_FOUNDRY_PROJECT_NAME is required for Agent Mode")
            
        # WebSocket Connection Management
        self.send_queue = asyncio.Queue()          # Queue for outgoing messages
        self.ws = None                             # Voice Live API WebSocket connection
        self.send_task = None                      # Background task for message sending
        self.incoming_websocket = None             # Client WebSocket connection
        self.is_raw_audio = True                   # Audio format flag
        self.is_response_active = False            # Response state tracking
        
        # Log successful initialization
        # NOTE: NO LOCAL ORCHESTRATION - this eliminates race conditions
        logger.info(f"VoiceLiveAgentHandler initialized for Azure AI Foundry Agent Mode")
        logger.info(f"Agent ID: {self.agent_id}, Project: {self.project_name}")
        logger.info("Race condition eliminated - using direct agent connection")

    def _generate_guid(self):
        """Generate a unique GUID for request tracking."""
        return str(uuid.uuid4())

    def get_azure_token(self) -> str:
        """Get Azure access token using DefaultAzureCredential (matching working demo)."""
        try:
            credential = DefaultAzureCredential()
            scopes = "https://ai.azure.com/.default"
            token = credential.get_token(scopes)
            return token.token
        except Exception as e:
            logger.error(f"Failed to get Azure token: {e}")
            raise

    async def connect(self):
        """Connects to Azure Voice Live API with Agent Mode support."""
        logger.info(f"Connecting to Voice Live API in Agent Mode")
        logger.info(f"Agent ID: {self.agent_id}")
        
        # Try agent_id parameter first (future Azure AI Foundry integration)
        try:
            await self._connect_with_agent_id()
        except Exception as e:
            logger.warning(f"Agent ID connection failed: {e}")
            logger.info("Falling back to model-based connection with agent instructions...")
            await self._connect_with_fallback()

    async def _connect_with_agent_id(self):
        """Try connecting with agent_id parameter (Azure AI Foundry native integration - matching working demo)."""
        # Get Azure access token (like working demo)
        access_token = self.get_azure_token()
        
        # Build WebSocket URL with correct parameter names (hyphens, not underscores!)
        azure_ws_endpoint = self.endpoint.rstrip("/").replace("https://", "wss://")
        url = (
            f"{azure_ws_endpoint}/voice-live/realtime?api-version=2025-05-01-preview"
            f"&agent-project-name={self.project_name}&agent-id={self.agent_id}"
            f"&agent-access-token={access_token}"
        )
        
        logger.info(f"Trying agent connection: {url.split('&agent-access-token=')[0]}...")  # Don't log token
        logger.info(f"Azure AI Foundry project: {self.project_name}")
        logger.info(f"Azure AI Foundry agent: {self.agent_id}")
        
        # Headers with Azure authentication (like working demo)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-ms-client-request-id": self._generate_guid()
        }
        
        self.ws = await ws_connect(url, additional_headers=headers)
        logger.info("Voice Live API connection established successfully (Native Agent Mode)")
        
        # Send session configuration (agent mode - no instructions)
        config = agent_session_config()
        logger.info(f"Sending agent session config (no instructions) for Azure AI Foundry agent: {self.agent_id}")
        await self._send_json(config)
        await self._initialize_connection("Native Azure AI Foundry Agent Mode")

    async def _connect_with_fallback(self):
        """Fallback connection using model parameter with agent-like instructions (API key auth)."""
        if not self.api_key:
            logger.error("Fallback mode requires AZURE_VOICE_LIVE_API_KEY")
            raise ValueError("API key required for fallback mode")
            
        url = f"{self.endpoint}/voice-live/realtime?api-version=2025-05-01-preview&model=gpt-4o-mini"
        url = url.replace("https://", "wss://")
        
        logger.info(f"Using fallback connection: {url}")
        
        headers = {
            "x-ms-client-request-id": self._generate_guid(),
            "api-key": self.api_key
        }
        
        self.ws = await ws_connect(url, additional_headers=headers)
        logger.info("Voice Live API connection established successfully (Fallback Mode)")
        
        # Send enhanced configuration with agent-like behavior
        config = session_config()
        config["session"]["instructions"] = f"""You are a healthcare appointment preparation assistant (fallback for Azure AI Foundry Agent {self.agent_id}). 

Your role is to help users prepare for medical appointments by:
1. Gathering information about their appointment and symptoms
2. Providing personalized checklists and preparation guidance
3. Helping organize questions for their healthcare provider

Maintain a supportive, professional tone and focus on appointment preparation logistics only. Never provide medical diagnosis or advice."""
        
        await self._send_json(config)
        await self._initialize_connection("Fallback Mode with Agent Instructions")

    async def _initialize_connection(self, mode_description):
        """Initialize the Voice Live connection with background tasks."""
        self.is_response_active = True
        await self._send_json({"type": "response.create"})

        # Start background tasks
        asyncio.create_task(self._receiver_loop())
        self.send_task = asyncio.create_task(self._sender_loop())
        
        logger.info(f"Voice Live handler initialized successfully ({mode_description})")
        logger.info("Race condition eliminated - no local orchestration competing with Voice Live")

    async def init_incoming_websocket(self, socket, is_raw_audio=True):
        """Sets up incoming client WebSocket."""
        self.incoming_websocket = socket
        self.is_raw_audio = is_raw_audio
        logger.info(f"Client WebSocket initialized - Agent Mode: {self.agent_id}")

    async def audio_to_voicelive(self, audio_b64: str):
        """Queues audio data to be sent to Voice Live API."""
        if audio_b64:
            await self.send_queue.put(
                json.dumps({"type": "input_audio_buffer.append", "audio": audio_b64})
            )

    async def _send_json(self, obj):
        """Sends a JSON object over WebSocket."""
        if self.ws:
            await self.ws.send(json.dumps(obj))

    async def _sender_loop(self):
        """Continuously sends messages from the queue to the Voice Live WebSocket."""
        try:
            while True:
                msg = await self.send_queue.get()
                if self.ws:
                    await self.ws.send(msg)
        except Exception:
            logger.exception("Voice Live sender loop error")

    async def _receiver_loop(self):
        """
        Handles incoming events from Voice Live WebSocket in Agent Mode.
        NO LOCAL ORCHESTRATION - Azure AI Foundry handles everything.
        """
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")

                match event_type:
                    case "session.created":
                        session_id = event.get("session", {}).get("id")
                        logger.info(f"Voice Live Agent Mode session created - Session ID: {session_id}")

                    case "input_audio_buffer.cleared":
                        logger.info("Audio buffer cleared for conversation reset")

                    case "input_audio_buffer.speech_started":
                        logger.info(f"Speech detection started - Audio start: {event.get('audio_start_ms')} ms")
                        await self.stop_audio()

                    case "input_audio_buffer.speech_stopped":
                        logger.info("Speech detection stopped - Azure AI Foundry agents processing")
                        flow_logger.agent_processing(f"agent_mode", "AzureAIFoundry", "speech_processing")

                    case "conversation.item.input_audio_transcription.completed":
                        transcript = event.get("transcript")
                        logger.info(f"User transcription: '{transcript}' - Azure AI Foundry agents handling")
                        # NO LOCAL ORCHESTRATION HERE - this eliminates race condition!
                        flow_logger.user_message("agent_mode", transcript, "voice")

                    case "conversation.item.input_audio_transcription.failed":
                        error_msg = event.get("error")
                        logger.warning(f"Transcription error: {error_msg}")

                    case "response.done":
                        response = event.get("response", {})
                        logger.info(f"Azure AI Foundry agent response completed: {response.get('id')}")
                        self.is_response_active = False
                        flow_logger.agent_response("agent_mode", "AzureAIFoundry", 0, has_card=False)

                    case "response.audio_transcript.done":
                        transcript = event.get("transcript")
                        logger.info(f"Azure AI Foundry agent said: {transcript}")
                        
                        # Send transcript to client
                        await self.send_message(
                            json.dumps({"Kind": "Transcription", "Text": transcript})
                        )

                    case "response.audio.delta":
                        delta = event.get("delta")
                        if self.is_raw_audio:
                            # For raw audio clients, convert to binary and send
                            audio_bytes = base64.b64decode(delta)
                            await self.send_message(audio_bytes)
                        else:
                            # For ACS clients, send as structured data
                            await self.voicelive_to_client(delta)

                    case "error":
                        logger.error(f"Voice Live Agent Mode error: {event}")
                        # Handle specific agent connection errors
                        if "agent" in str(event.get("error", {})).lower():
                            logger.error("Agent connection error - check Azure AI Foundry configuration")

                    case _:
                        logger.debug(f"Other Voice Live Agent Mode event: {event_type}")
                        
        except Exception as e:
            logger.exception("Voice Live Agent Mode receiver loop error")
            logger.error(f"Error details: {e}")

    async def send_message(self, message: Data):
        """Sends data back to client WebSocket."""
        try:
            if self.incoming_websocket:
                if isinstance(message, bytes):
                    await self.incoming_websocket.send_bytes(message)
                elif isinstance(message, str):
                    await self.incoming_websocket.send_text(message)
                elif isinstance(message, dict):
                    await self.incoming_websocket.send_text(json.dumps(message))
                else:
                    await self.incoming_websocket.send_text(str(message))
        except Exception:
            logger.exception("Failed to send message to client")

    async def voicelive_to_client(self, base64_data):
        """Converts Voice Live audio delta to client audio message."""
        try:
            data = {
                "Kind": "AudioData",
                "AudioData": {"Data": base64_data},
                "StopAudio": None,
            }
            await self.send_message(json.dumps(data))
        except Exception:
            logger.exception("Error in voicelive_to_client")

    async def stop_audio(self):
        """Sends a StopAudio signal to client."""
        if not self.is_raw_audio:
            stop_audio_data = {"Kind": "StopAudio", "AudioData": None, "StopAudio": {}}
            await self.send_message(json.dumps(stop_audio_data))

    async def web_to_voicelive(self, audio_bytes):
        """Encodes raw audio bytes from web client and sends to Voice Live API."""
        if isinstance(audio_bytes, bytes):
            audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            await self.audio_to_voicelive(audio_b64)

    async def close(self):
        """Clean up resources."""
        try:
            if self.send_task:
                self.send_task.cancel()
            if self.ws:
                await self.ws.close()
        except Exception:
            logger.exception("Error closing Voice Live Agent Mode handler")