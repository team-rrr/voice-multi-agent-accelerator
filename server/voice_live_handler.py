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
from logging_config import ConversationFlowLogger, setup_professional_logging

# Set up professional logging
setup_professional_logging(level="INFO")
logger = logging.getLogger(__name__)
flow_logger = ConversationFlowLogger(__name__)


def session_config():
    """Returns the default session configuration for Voice Multi-Agent Assistant."""
    return {
        "type": "session.update",
        "session": {
            "instructions": "You are a text-to-speech service. Only synthesize the exact text provided to you - do not generate additional content or responses. When connecting, say: 'Voice Multi-Agent Assistant is ready! You can start speaking to get personalized appointment preparation help.'",
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
        self.is_response_active = False
        self.pending_responses = asyncio.Queue()
        self.pending_card_data = None
        
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
            logger.info("Voice Live API connection established successfully")

            # Send initial session configuration
            await self._send_json(session_config())
            self.is_response_active = True
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
        logger.info(f"Client WebSocket initialized - Audio format: {'raw' if is_raw_audio else 'processed'}")

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
                        logger.info(f"Voice Live session created - Session ID: {session_id}")

                    case "input_audio_buffer.cleared":
                        logger.info("Audio buffer cleared for conversation reset")

                    case "input_audio_buffer.speech_started":
                        logger.info(f"Speech detection started - Audio start: {event.get('audio_start_ms')} ms")
                        await self.stop_audio()

                    case "input_audio_buffer.speech_stopped":
                        logger.info("Speech detection stopped - Processing user input")

                    case "conversation.item.input_audio_transcription.completed":
                        transcript = event.get("transcript")
                        logger.info(f"User transcription completed - Text: '{transcript}'")
                        
                        # Skip processing if there's already an active response
                        if self.is_response_active:
                            logger.info("Transcription processing skipped - Active response in progress")
                            return
                        
                        if self.on_final_transcription:
                            # A callback is defined, so run the full orchestration
                            logger.info("Final transcription received. Calling orchestrator...")
                            
                            try:
                                # Skip orchestration for very short or unclear inputs
                                if len(transcript.strip()) < 3:
                                    logger.info("Skipping orchestration for very short input")
                                    return
                                
                                # This calls the run_orchestration function
                                response = await self.on_final_transcription(transcript)
                                logger.info("Orchestrator processing completed - Sending response to Voice Live API")

                                # Send the spoken text part FIRST to be synthesized by Voice Live
                                await self.text_to_voicelive(response.spoken)
                                
                                # Also send the AI response to client for conversation logging
                                await self.send_message({
                                    "type": "ai_response", 
                                    "text": response.spoken
                                })
                                
                                # Schedule card to be sent when response completes (if card exists)
                                if response.card:
                                    # Store card data to send after response completion
                                    self.pending_card_data = response.card
                                    logger.info("Multi-agent response with card scheduled for post-speech delivery")
                                    
                                    # Also set a fallback timer in case response.done isn't received
                                    asyncio.create_task(self._fallback_card_delivery(response.card, 3.0))
                                else:
                                    logger.info("Multi-agent response sent (no card)")
                                
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
                        self.is_response_active = False
                        
                        # Trigger any pending card sends now that speech is complete
                        if hasattr(self, 'pending_card_data') and self.pending_card_data:
                            card_data = self.pending_card_data
                            self.pending_card_data = None
                            # Send card immediately after response completion
                            asyncio.create_task(self._send_card_immediately(card_data))
                        
                        # Process any pending responses
                        await self._process_next_response()
                        
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
                # Log outgoing messages (truncate audio data for readability)
                if isinstance(message, dict):
                    msg_type = message.get("type", "unknown")
                    if msg_type == "card":
                        logger.info(f"🔔 Sending to client: type={msg_type}, payload keys={list(message.get('payload', {}).keys())}")
                    elif msg_type != "AudioData":  # Don't spam with audio messages
                        logger.info(f"📤 Sending to client: type={msg_type}")
                        
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
        """Sends text message to Voice Live API for processing with response conflict prevention."""
        try:
            # Always queue responses to prevent conflicts
            logger.info(f"Queueing text response for sequential processing: {text[:50]}...")
            await self.pending_responses.put(text)
            
            # If no response is currently active, process immediately
            if not self.is_response_active:
                await self._process_next_response()
            
        except Exception:
            logger.exception("Error sending text to Voice Live API")
            
    async def _process_next_response(self):
        """Process the next queued response if no response is currently active."""
        try:
            if not self.is_response_active and not self.pending_responses.empty():
                text = await self.pending_responses.get()
                await self._send_text_immediately(text)
        except Exception:
            logger.exception("Error processing next response")
            
    async def _send_text_immediately(self, text: str):
        """Immediately sends text to Voice Live API for text-to-speech synthesis."""
        try:
            self.is_response_active = True
            
            # Create an assistant message (not user message) to be synthesized directly
            assistant_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            }
            await self._send_json(assistant_message)
            
            # Request response generation to synthesize the assistant message
            await self._send_json({"type": "response.create"})
            logger.info(f"Sent text to Voice Live for TTS: {text}")
        except Exception:
            self.is_response_active = False
            logger.exception("Error sending text immediately to Voice Live API")

    async def _send_card_immediately(self, card_payload: dict):
        """Send card data immediately after speech response completion."""
        try:
            # Only send card if we still have a websocket connection
            if self.incoming_websocket:
                logger.info(f"Sending card message: type=card, payload={card_payload}")
                await self.send_message({
                    "type": "card",
                    "payload": card_payload
                })
                logger.info("Card delivery completed - Sent immediately after speech response")
            else:
                logger.warning("Cannot send card - websocket connection lost")
            
        except Exception as e:
            logger.error(f"Error sending immediate card: {e}")

    async def _fallback_card_delivery(self, card_payload: dict, delay_seconds: float = 3.0):
        """Fallback card delivery in case response.done event isn't received."""
        try:
            # Wait for a reasonable time for normal completion
            await asyncio.sleep(delay_seconds)
            
            # If card is still pending, send it now
            if hasattr(self, 'pending_card_data') and self.pending_card_data is not None:
                if self.incoming_websocket:
                    await self.send_message({
                        "type": "card",
                        "payload": card_payload
                    })
                    self.pending_card_data = None
                    logger.info(f"Card sent via fallback delivery after {delay_seconds}s")
                else:
                    logger.warning("Cannot send fallback card - websocket connection lost")
            
        except Exception as e:
            logger.error(f"Error in fallback card delivery: {e}")

    async def _send_card_with_delay(self, card_payload: dict, query: str, delay_seconds: float = 1.5):
        """Send card data after a delay to allow speech synthesis to start first."""
        try:
            # Wait for speech to begin before showing card
            await asyncio.sleep(delay_seconds)
            
            # Only send card if we still have a websocket connection
            if self.incoming_websocket:
                await self.send_message({
                    "type": "card",
                    "payload": card_payload
                })
                logger.info(f"Card sent after {delay_seconds}s delay for better UX timing")
            else:
                logger.warning("Cannot send card - websocket connection lost")
            
        except Exception as e:
            logger.error(f"Error sending delayed card: {e}")

    async def close(self):
        """Clean up resources."""
        try:
            if self.send_task:
                self.send_task.cancel()
            if self.ws:
                await self.ws.close()
        except Exception:
            logger.exception("Error closing Voice Live handler")