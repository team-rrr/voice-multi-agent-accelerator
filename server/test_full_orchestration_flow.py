import asyncio, json
import voice_live_handler

async def main():
    cfg = {"AZURE_VOICE_LIVE_ENDPOINT":"wss://example.invalid","VOICE_LIVE_MODEL":"m","AZURE_VOICE_LIVE_API_KEY":"k"}
    h = voice_live_handler.VoiceLiveHandler(cfg)

    async def fake_send_json(obj):
        print("TO_VOICE_LIVE:", json.dumps(obj))
    h._send_json = fake_send_json

    async def fake_send_message(msg):
        print("TO_FRONTEND:", msg)
    h.send_message = fake_send_message

    # Simulate that there's an initial active response from elsewhere
    h.is_response_active = True
    h._service_active_response = True

    # Prepare orchestrated response and card
    orchestrated_text = "Please bring your medication list and arrive 15 minutes early."
    card = {"title": "Appointment Prep", "preparation_items": ["Medication list", "Photo ID"]}

    # Set pending card as orchestration would
    h.pending_card_data = card

    # Create the event used to wait for response.done
    h._orchestrated_response_event = asyncio.Event()

    print("--- Enqueue orchestrated TTS ---")
    await h.text_to_voicelive(orchestrated_text)
    print("pending_responses empty after enqueue:", h.pending_responses.empty())

    # Simulate first response.done from service (clearing previous active response)
    print("--- Simulate first response.done (clears previous active response) ---")
    # Receiver would clear service flags and then call _process_next_response
    h._service_active_response = False
    h.is_response_active = False
    await h._process_next_response()

    # At this point the queued orchestrated TTS should have been sent (and new response started)
    print("--- After processing queued TTS ---")
    print("is_response_active:", h.is_response_active)
    print("orchestrated_response_active:", h.orchestrated_response_active)
    print("pending_responses empty:", h.pending_responses.empty())

    # Now simulate response.done for the orchestrated TTS so card is delivered
    print("--- Simulate second response.done (orchestrated TTS completed) ---")
    # Emulate the receiver behavior
    if h.orchestrated_response_active:
        h.is_response_active = False
        h.orchestrated_response_active = False
        # Trigger card send (as receiver would)
        if hasattr(h, 'pending_card_data') and h.pending_card_data:
            card_data = h.pending_card_data
            h.pending_card_data = None
            await h._send_card_immediately(card_data)

    print("--- Final state ---")
    print("is_response_active:", h.is_response_active)
    print("orchestrated_response_active:", h.orchestrated_response_active)
    print("pending_responses empty:", h.pending_responses.empty())

if __name__ == '__main__':
    asyncio.run(main())
