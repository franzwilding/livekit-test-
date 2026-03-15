FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

# Pre-download VAD model
RUN python -c "from livekit.plugins import silero; silero.VAD.load()"

CMD ["python", "src/agent.py", "start"]
