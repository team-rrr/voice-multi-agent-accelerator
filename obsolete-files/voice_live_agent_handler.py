"""
Solution B: Azure AI Foundry Agent Mode Handler
Eliminates race condition by connecting di        try:
            self.ws = await ws_connect(url, additional_headers=headers)
            logger.info("Voice Live API connection established successfully (Agent Mode)")

            # Send agent configuration to link with Azure AI Foundry
            agent_config = {
                "type": "agent.configure",
                "agent_id": self.agent_id,
                "azure_ai_foundry": {
                    "endpoint": self.config.get("AZURE_AI_FOUNDRY_ENDPOINT"),
                    "project_id": self.config.get("AZURE_AI_PROJECT_ID", "voice-multi-agent-project")
                }
            }
            await self._send_json(agent_config)
            
            # Send initial session configuration for agent mode
            await self._send_json(session_config())
            self.is_response_active = True
            await self._send_json({"type": "response.create"})

            # Start background tasks
            asyncio.create_task(self._receiver_loop())
            self.send_task = asyncio.create_task(self._sender_loop())
            
            logger.info("Voice Live Agent Mode handler initialized successfully - Race condition eliminated")
            
        except Exception as e:
            logger.error(f"Failed to connect to Voice Live API (Agent Mode): {e}")
            raise Foundry agents
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
    return {
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


class VoiceLiveAgentHandler:
    """
    Solution B: Manages audio streaming using Azure AI Foundry Agent Mode.
    Eliminates race condition by using agent_id instead of model parameter.
    """

    def __init__(self, config):
        self.endpoint = config["AZURE_VOICE_LIVE_ENDPOINT"]
        self.agent_id = config["VOICE_LIVE_AGENT_ID"]  # Azure AI Foundry agent
        self.api_key = config["AZURE_VOICE_LIVE_API_KEY"]
        self.client_id = config.get("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        self.config = config  # Store full config for Azure AI Foundry connection
        self.send_queue = asyncio.Queue()
        self.ws = None
        self.send_task = None
        self.incoming_websocket = None
        self.is_raw_audio = True
        self.is_response_active = False
        self.pending_responses = asyncio.Queue()
        self.pending_card_data = None
        
        logger.info(f"VoiceLiveAgentHandler initialized with Azure AI Foundry Agent: {self.agent_id}")

    def _generate_guid(self):
        """Generate a unique GUID for request tracking."""
        return str(uuid.uuid4())

    async def connect(self):
        """Connects to Azure Voice Live API via WebSocket using agent_id mode."""
        # SOLUTION B: Use Voice Live API with agent_id parameter to eliminate race condition
        # The Voice Live API is still hosted by Speech Service, but we pass agent_id instead of model
        url = f"{self.endpoint}/voice-live/realtime?api-version=2025-05-01-preview&agent_id={self.agent_id}"
        url = url.replace("https://", "wss://")

        headers = {
            "x-ms-client-request-id": self._generate_guid(),
            # Include Azure AI Foundry project information for agent connection
            "x-ms-ai-foundry-endpoint": self.config.get("AZURE_AI_FOUNDRY_ENDPOINT", ""),
            "x-ms-ai-foundry-key": self.config.get("AZURE_AI_FOUNDRY_API_KEY", "")
        }

        # Use Speech Service API key for Voice Live connection
        headers["api-key"] = self.api_key
        logger.info(f"Connecting to Voice Live API with Agent Mode - Agent ID: {self.agent_id}")
        logger.info(f"Azure AI Foundry integration: {self.config.get('AZURE_AI_FOUNDRY_ENDPOINT', 'not configured')}")

        try:
            self.ws = await ws_connect(url, additional_headers=headers)
            logger.info("Voice Live API connection established successfully (Agent Mode)")

            # Send initial session configuration
            await self._send_json(session_config())
            self.is_response_active = True
            await self._send_json({"type": "response.create"})

            # Start background tasks
            asyncio.create_task(self._receiver_loop())
            self.send_task = asyncio.create_task(self._sender_loop())
            
            logger.info("Voice Live Agent Mode handler initialized successfully - Race condition eliminated")
            
        except Exception as e:
            logger.error(f"Failed to connect to Voice Live API (Agent Mode): {e}")
            raise

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
        """Handles incoming events from the Voice Live WebSocket (Agent Mode)."""
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
                        logger.info("Speech detection stopped - Azure AI agents will process")

                    case "conversation.item.input_audio_transcription.completed":
                        transcript = event.get("transcript")
                        logger.info(f"User transcription completed - Agent processing: '{transcript}'")
                        
                        # In Agent Mode, Azure AI Foundry handles the processing automatically
                        # No local orchestration needed - eliminates race condition!
                        flow_logger.agent_processing(f"agent_mode", "AzureAIFoundry", "agent_chain_processing")

                    case "conversation.item.input_audio_transcription.failed":
                        error_msg = event.get("error")
                        logger.warning(f"Transcription error: {error_msg}")

                    case "response.done":
                        response = event.get("response", {})
                        logger.info(f"Azure AI Foundry response completed: {response.get('id')}")
                        self.is_response_active = False
                        
                        # In agent mode, check if response contains card data
                        await self._handle_agent_response_completion(response)
                        
                        if response.get("status_details"):
                            logger.debug(
                                f"Status details: {json.dumps(response['status_details'], indent=2)}"
                            )

                    case "response.audio_transcript.done":
                        transcript = event.get("transcript")
                        logger.info(f"Azure AI agent said: {transcript}")
                        flow_logger.agent_response("agent_mode", "AzureAIFoundry", len(transcript), has_card=False)
                        
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

                    case _:
                        logger.debug(f"Other Voice Live Agent Mode event: {event_type}")
        except Exception:
            logger.exception("Voice Live Agent Mode receiver loop error")

    async def _handle_agent_response_completion(self, response):
        """Handle completion of Azure AI Foundry agent response."""
        try:
            # In future versions, check response for card data from Azure AI agents
            # For now, agent responses are purely conversational
            logger.info("Azure AI Foundry agent response completed successfully")
            
        except Exception as e:
            logger.error(f"Error handling agent response completion: {e}")

    async def send_message(self, message: Data):
        """Sends data back to client WebSocket."""
        try:
            if self.incoming_websocket:
                # Check if message is bytes (audio data)
                if isinstance(message, bytes):
                    await self.incoming_websocket.send_bytes(message)
                # Check if message is a string (JSON text)
                elif isinstance(message, str):
                    await self.incoming_websocket.send_text(message)
                # Check if message is a dict (convert to JSON)
                elif isinstance(message, dict):
                    await self.incoming_websocket.send_text(json.dumps(message))
                else:
                    # Fallback - try to send as text
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