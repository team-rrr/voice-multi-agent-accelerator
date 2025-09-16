from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="Voice Multi-Agent Accelerator Backend", version="0.1.0")

@app.get("/healthz")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "voice-multi-agent-accelerator", "openai_enabled": bool(os.getenv("AZURE_OPENAI_ENDPOINT"))})

@app.get("/")
def root() -> JSONResponse:
    return JSONResponse({"message": "Voice Multi-Agent Accelerator backend running"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("APP_PORT", "8000")))
