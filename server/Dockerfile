FROM mcr.microsoft.com/devcontainers/python:3.12

# Allow statements and log messages to immediately appear
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    APP_PORT=8000

WORKDIR /app

# Copy dependency manifests first (better layer caching)
COPY pyproject.toml poetry.lock* uv.lock* ./

RUN pip install --upgrade pip setuptools wheel \
    && pip install "poetry==$POETRY_VERSION" \
    && if [ -f pyproject.toml ]; then poetry export -f requirements.txt --output requirements.txt --without-hashes; fi \
    && pip install -r requirements.txt \
    && pip uninstall -y poetry || true

COPY . .

EXPOSE 8000

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
