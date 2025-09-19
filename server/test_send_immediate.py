import asyncio, json
import voice_live_handler

async def run_test():
    cfg = {"AZURE_VOICE_LIVE_ENDPOINT":"wss://example.invalid","VOICE_LIVE_MODEL":"m","AZURE_VOICE_LIVE_API_KEY":"k"}
    h = voice_live_handler.VoiceLiveHandler(cfg)

    async def fake_send_json(obj):
        print("TO_VOICE_LIVE:", json.dumps(obj))
    h._send_json = fake_send_json

    # Call _send_text_immediately directly
    await h._send_text_immediately("Test immediate TTS message from orchestrator")
    print("state after:", h.is_response_active, h.orchestrated_response_active)

if __name__ == '__main__':
    asyncio.run(run_test())
