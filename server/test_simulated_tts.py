import asyncio, json
import voice_live_handler

class MockResp:
    def __init__(self, spoken, card=None):
        self.spoken = spoken
        self.card = card

async def main():
    config = {
        "AZURE_VOICE_LIVE_ENDPOINT": "wss://example.invalid",
        "VOICE_LIVE_MODEL": "test-model",
        "AZURE_VOICE_LIVE_API_KEY": "fake-key"
    }

    h = voice_live_handler.VoiceLiveHandler(config)

    # Patch network methods to print instead of sending
    async def fake_send_json(obj):
        print("TO_VOICE_LIVE:", json.dumps(obj))
    h._send_json = fake_send_json

    async def fake_send_message(msg):
        print("TO_FRONTEND:", msg)
    h.send_message = fake_send_message

    # Simulate orchestration response
    resp = MockResp("Hello from orchestrator", {"title": "Test Card", "preparation_items": ["Bring EKG", "Bring meds"]})

    # Emulate the orchestration flow: create event and flags, then send TTS
    h._orchestrated_response_event = asyncio.Event()
    h.is_response_active = True
    h.orchestrated_response_active = True

    print("--- BEFORE text_to_voicelive ---")
    print("is_response_active:", h.is_response_active, "orchestrated_response_active:", h.orchestrated_response_active)

    # Call text_to_voicelive which queues and triggers processing
    await h.text_to_voicelive(resp.spoken)

    print("--- AFTER text_to_voicelive (queued) ---")
    print("pending_responses empty:", h.pending_responses.empty())

    # Wait a bit to let _process_next_response run (it runs in same loop)
    await asyncio.sleep(0.2)

    print("--- Simulating response.done from service (setting event) ---")
    # Simulate the service signaling completion
    try:
        h._orchestrated_response_event.set()
    except Exception as e:
        print("Error setting event:", e)

    # Emulate receiver-side response.done handling: clear active flags and process next queued response
    h.is_response_active = False
    h.orchestrated_response_active = False
    # Explicitly call processing of queued responses (what receiver would do)
    await h._process_next_response()

    print("--- FINAL STATE ---")
    print("is_response_active:", h.is_response_active)
    print("orchestrated_response_active:", h.orchestrated_response_active)
    print("pending_responses empty:", h.pending_responses.empty())

if __name__ == '__main__':
    asyncio.run(main())
