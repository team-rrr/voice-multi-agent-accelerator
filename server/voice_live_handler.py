"""
Voice Live API Handler for Voice Multi-Agent Echo Bot
Based on the working implementation from call-center-voice-agent-accelerator
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import Optional

from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Data

logger = logging.getLogger(__name__)


def session_config():
    """Returns the default session configuration for Voice Multi-Agent Assistant."""
    return {
        "type": "session.update",
        "session": {
            "instructions": "You are a Voice Multi-Agent Assistant that helps users prepare for medical appointments. When connecting, say: 'Voice Multi-Agent Assistant is ready! You can start speaking to get personalized appointment preparation help.'",
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
                "temperature": 0.8,
            },
            "input_audio_transcription": {
                "model": "whisper-1"
            },
        },
    }


class VoiceLiveHandler:
    """Manages audio streaming between WebSocket client and Azure Voice Live API."""

    def __init__(self, config, on_final_transcription=None):
        self.endpoint = config["AZURE_VOICE_LIVE_ENDPOINT"]
        self.model = config["VOICE_LIVE_MODEL"]
        self.api_key = config["AZURE_VOICE_LIVE_API_KEY"]
        self.client_id = config.get("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        self.send_queue = asyncio.Queue()
        self.ws = None
        self.send_task = None
        self.incoming_websocket = None
        self.is_raw_audio = True
        self.on_final_transcription = on_final_transcription

        # Debug log to confirm orchestration callback is set
        if self.on_final_transcription:
            logger.info("VoiceLiveHandler initialized WITH multi-agent orchestration callback")
        else:
            logger.info("VoiceLiveHandler initialized WITHOUT orchestration callback (will use echo mode)")

    def _generate_guid(self):
        """Generate a unique GUID for request tracking."""
        return str(uuid.uuid4())

    async def connect(self):
        """Connects to Azure Voice Live API via WebSocket."""
        url = f"{self.endpoint}/voice-live/realtime?api-version=2025-05-01-preview&model={self.model}"
        url = url.replace("https://", "wss://")

        headers = {"x-ms-client-request-id": self._generate_guid()}

        # For local development, use API key
        # In production deployment, this would use managed identity
        headers["api-key"] = self.api_key
        logger.info("Using API Key authentication for Voice Live API")

        try:
            self.ws = await ws_connect(url, additional_headers=headers)
            logger.info("✅ Connected to Voice Live API")

            # Send initial session configuration
            await self._send_json(session_config())
            await self._send_json({"type": "response.create"})

            # Start background tasks
            asyncio.create_task(self._receiver_loop())
            self.send_task = asyncio.create_task(self._sender_loop())

            logger.info("Voice Live API handler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Voice Live API: {e}")
            raise

    async def init_incoming_websocket(self, socket, is_raw_audio=True):
        """Sets up incoming client WebSocket."""
        self.incoming_websocket = socket
        self.is_raw_audio = is_raw_audio
        logger.info(f"Initialized client WebSocket (raw_audio={is_raw_audio})")

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
        """Handles incoming events from the Voice Live WebSocket."""
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")

                match event_type:
                    case "session.created":
                        session_id = event.get("session", {}).get("id")
                        logger.info(f"Voice Live session created: {session_id}")

                    case "input_audio_buffer.cleared":
                        logger.debug("Input audio buffer cleared")

                    case "input_audio_buffer.speech_started":
                        logger.info(
                            f"Speech started at {event.get('audio_start_ms')} ms"
                        )
                        await self.stop_audio()

                    case "input_audio_buffer.speech_stopped":
                        logger.info("Speech stopped")

                    case "conversation.item.input_audio_transcription.completed":
                        transcript = event.get("transcript")
                        logger.info(f"User said: {transcript}")

                        if self.on_final_transcription:
                            # A callback is defined, so run the full orchestration
                            logger.info("Final transcription received. Calling orchestrator...")

                            try:
                                # Skip orchestration for very short or unclear inputs
                                if len(transcript.strip()) < 3:
                                    logger.info("Skipping orchestration for very short input")
                                    return

                                # This calls the run_orchestration function from Day 3
                                response = await self.on_final_transcription(transcript)
                                logger.info("Orchestration response received, sending to Voice Live...")

                                # Send the spoken text part to be synthesized by Voice Live
                                await self.text_to_voicelive(response.spoken)

                                # Build agent/function call trace for frontend logging
                                agent_trace = [
                                    {"name": "CaregiverPlugin.InfoAgent", "function": "InfoAgent"},
                                    {"name": "CaregiverPlugin.PatientContextAgent", "function": "PatientContextAgent"},
                                    {"name": "CardiologyAgent.extract_symptoms", "function": "extract_symptoms"},
                                    {"name": "CardiologyAgent.recommend_tests", "function": "recommend_tests"},
                                    {"name": "CaregiverPlugin.ActionAgent", "function": "ActionAgent"}
                                ]

                                # Send orchestration_response with agent trace and card data
                                await self.send_message({
                                    "type": "orchestration_response",
                                    "spoken_response": response.spoken,
                                    "card_data": {
                                        **response.card,
                                        "agents": agent_trace
                                    }
                                })
                                logger.info("Multi-agent orchestration_response sent with agent trace and card data")

                            except Exception as e:
                                logger.error(f"Orchestration failed: {e}")
                                # Fallback to a helpful message
                                await self.text_to_voicelive("I apologize, but I'm having trouble processing your request right now. Please try again.")
                                await self.send_message({
                                    "type": "error",
                                    "text": f"Orchestration error: {str(e)}"
                                })

                        else:
                            # No callback, so just perform a simple echo (fallback behavior)
                            logger.info(f"No orchestrator callback. Echoing: {transcript}")
                            await self.text_to_voicelive(transcript)

                    case "conversation.item.input_audio_transcription.failed":
                        error_msg = event.get("error")
                        logger.warning(f"Transcription error: {error_msg}")

                    case "response.done":
                        response = event.get("response", {})
                        logger.info(f"Response completed: {response.get('id')}")
                        if response.get("status_details"):
                            logger.debug(
                                f"Status details: {json.dumps(response['status_details'], indent=2)}"
                            )

                    case "response.audio_transcript.done":
                        transcript = event.get("transcript")
                        logger.info(f"AI said: {transcript}")
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
                        logger.error(f"Voice Live error: {event}")

                    case _:
                        logger.debug(f"Other Voice Live event: {event_type}")
        except Exception:
            logger.exception("Voice Live receiver loop error")

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

    async def text_to_voicelive(self, text: str):
        """Sends text message to Voice Live API for processing."""
        try:
            # Create a conversation item with user text
            user_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text
                        }
                    ]
                }
            }
            await self._send_json(user_message)
            # Request response generation
            await self._send_json({"type": "response.create"})
            logger.info(f"Sent text to Voice Live: {text}")
        except Exception:
            logger.exception("Error sending text to Voice Live API")

    async def close(self):
        """Clean up resources."""
        try:
            if self.send_task:
                self.send_task.cancel()
            if self.ws:
                await self.ws.close()
        except Exception:
            logger.exception("Error closing Voice Live handler")