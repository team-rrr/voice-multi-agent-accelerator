"""
Solution B: Azure AI Foundry Agent Mode Handler
Eliminates race condition by connecting directly to Azure AI Foundry agents
Provides WebSocket integration between Voice Live API and Azure AI Foundry multi-agent system
"""

import asyncio
import base64
import json
import logging
import uuid
import os
from typing import Optional

from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Data
from logging_config import ConversationFlowLogger, setup_professional_logging

# Set up professional logging
setup_professional_logging(level="INFO")
logger = logging.getLogger(__name__)
flow_logger = ConversationFlowLogger(__name__)


def session_config():
    """Returns the session configuration for Azure AI Foundry Agent Mode."""
    # Get Azure AI Foundry configuration
    project_id = os.getenv("AZURE_AI_PROJECT_ID", "voice-multi-agent-project")
    foundry_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
    foundry_connection_string = os.getenv("AZURE_AI_FOUNDRY_CONNECTION_STRING")
    
    config = {
        "type": "session.update",
        "session": {
            "instructions": "You are connected to an Azure AI Foundry multi-agent system for healthcare appointment preparation. Follow the agent orchestration exactly as configured.",
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
                "name": "en-US-Ava:DragonHDLatestNeural",
                "type": "azure-standard", 
                "temperature": 0.1,
            },
            "input_audio_transcription": {
                "model": "whisper-1"
            },
        },
    }
    
    # Note: Azure AI Foundry project configuration is handled via URL parameters
    # The agent_id and project_name are passed in the WebSocket URL
    logger.info(f"Session configuration prepared for Azure AI Foundry Agent Mode")
    
    return config


class VoiceLiveAgentHandler:
    """
    Solution B: Azure AI Foundry Agent Mode Handler.
    Direct agent integration eliminating race conditions by removing local orchestration entirely.
    """

    def __init__(self, config):
        # Basic Voice Live API configuration
        self.endpoint = config["AZURE_VOICE_LIVE_ENDPOINT"]
        self.api_key = config["AZURE_VOICE_LIVE_API_KEY"]
        self.client_id = config.get("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        
        # Azure AI Foundry Agent ID (from environment)
        self.agent_id = os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")
        if not self.agent_id:
            logger.error("AZURE_AI_FOUNDRY_AGENT_ID is not set! Agent mode requires this.")
            raise ValueError("AZURE_AI_FOUNDRY_AGENT_ID is required for Agent Mode")
            
        # WebSocket management
        self.send_queue = asyncio.Queue()
        self.ws = None
        self.send_task = None
        self.incoming_websocket = None
        self.is_raw_audio = True
        self.is_response_active = False
        
        # NO LOCAL ORCHESTRATION - this eliminates the race condition
        logger.info(f"VoiceLiveAgentHandler initialized for AI Foundry Agent Mode")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info("Race condition eliminated - no local orchestration callback")

    def _generate_guid(self):
        """Generate a unique GUID for request tracking."""
        return str(uuid.uuid4())

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
        """Try connecting with agent_id parameter (Azure AI Foundry native integration)."""
        # Add Azure AI Foundry project configuration
        project_name = os.getenv("AZURE_AI_FOUNDRY_PROJECT_NAME", "voice-multi-agent-project")
        project_id = os.getenv("AZURE_AI_PROJECT_ID", "voice-multi-agent-project")
        foundry_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        
        # Validate Azure AI Foundry configuration
        if not project_name and not project_id:
            logger.error("Azure AI Foundry project configuration missing!")
            logger.error("Required: Either AZURE_AI_FOUNDRY_PROJECT_NAME or AZURE_AI_PROJECT_ID")
            raise ValueError("Azure AI Foundry project configuration incomplete")
        
        # Use project_name in URL as per Azure documentation
        project_param = project_name or project_id
        url = f"{self.endpoint}/voice-live/realtime?api-version=2025-05-01-preview&agent_id={self.agent_id}&project_name={project_param}"
        url = url.replace("https://", "wss://")
        
        logger.info(f"Trying agent_id connection: {url}")
        logger.info(f"Azure AI Foundry project: {project_param}")
        
        headers = {"x-ms-client-request-id": self._generate_guid()}
        headers["api-key"] = self.api_key
        
        self.ws = await ws_connect(url, additional_headers=headers)
        logger.info("Voice Live API connection established successfully (Native Agent Mode)")
        
        # Send session configuration (agent_id and project already in URL)
        config = session_config()
        logger.info(f"Sending session config for Azure AI Foundry agent: {self.agent_id}")
        await self._send_json(config)
        await self._initialize_connection("Native Azure AI Foundry Agent Mode")

    async def _connect_with_fallback(self):
        """Fallback connection using model parameter with agent-like instructions."""
        url = f"{self.endpoint}/voice-live/realtime?api-version=2025-05-01-preview&model=gpt-4o-mini"
        url = url.replace("https://", "wss://")
        
        logger.info(f"Using fallback connection: {url}")
        
        headers = {"x-ms-client-request-id": self._generate_guid()}
        headers["api-key"] = self.api_key
        
        self.ws = await ws_connect(url, additional_headers=headers)
        logger.info("Voice Live API connection established successfully (Fallback Mode)")
        
        # Send enhanced configuration with agent-like behavior
        config = session_config()
        config["session"]["instructions"] = f"""You are a healthcare appointment preparation assistant connected to Azure AI Foundry Agent {self.agent_id}. 

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