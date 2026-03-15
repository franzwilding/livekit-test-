FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY configs/ configs/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Download VAD model
RUN python -c "from livekit.plugins import silero; silero.VAD.load()"

EXPOSE 8080

CMD ["python", "src/agent.py", "start"]
