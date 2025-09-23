FROM mcr.microsoft.com/devcontainers/python:3.12

# Allow statements and log messages to immediately appear
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    APP_PORT=8000

WORKDIR /app

# Copy dependency manifests first (better layer caching)
COPY requirements.txt ./

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "app_voice_live_agent_mode:app", "--host", "0.0.0.0", "--port", "8000"]
