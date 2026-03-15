# AI Voice Agent

A production-ready AI Voice Agent built with [LiveKit Agents](https://docs.livekit.io/agents/) (Python) and [LiveKit Agents UI](https://livekit.io/ui) (React/Next.js). Fully configurable STT, TTS, LLM providers with emotional intelligence, turn detection, interruption handling, and tool calling.

## Features

- **Real-time voice conversations** via WebRTC (LiveKit)
- **Configurable speech pipeline**: STT (Deepgram, OpenAI) → LLM (OpenAI GPT-4o, Anthropic Claude) → TTS (OpenAI, ElevenLabs)
- **Turn detection**: Multilingual turn detector with interruption support (barge-in)
- **Emotional intelligence**: Detects user emotions and adapts responses accordingly
- **Tool calling**: Built-in tools + configurable webhook-based tools
- **Beautiful UI**: Dark theme with audio visualizer, real-time transcript, config panel
- **YAML configuration**: Change models, prompts, and tools without code changes
- **Production-ready**: Docker support, comprehensive tests, error handling

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm
- A [LiveKit Cloud](https://cloud.livekit.io) account (free tier available)
- API keys for your chosen providers (OpenAI, Deepgram, etc.)

### 1. Clone and configure

```bash
# Clone the repo
git clone <repo-url>
cd livekit-test-

# Set up backend environment
cp agent/.env.example agent/.env
# Edit agent/.env with your LiveKit and API keys

# Set up frontend environment
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your LiveKit credentials
```

### 2. Start the backend agent

```bash
cd agent

# Install dependencies
pip install -e ".[dev]"

# Download required models (VAD, turn detector)
python src/agent.py download-files

# Run in development mode
python src/agent.py dev
```

### 3. Start the frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Connect and talk

Click "Connect" on the welcome screen. The agent will greet you and you can start talking!

## Configuration

All agent behavior is configured via `agent/configs/default.yaml`:

### Models

```yaml
# Speech-to-Text
stt:
  provider: "deepgram"  # or "openai"
  model: "nova-3"
  language: "multi"

# Text-to-Speech
tts:
  provider: "openai"    # or "elevenlabs"
  model: "gpt-4o-mini-tts"
  voice: "coral"

# LLM
llm:
  provider: "openai"    # or "anthropic"
  model: "gpt-4o"
  temperature: 0.7
```

### System Prompt

```yaml
agent:
  system_prompt: |
    You are a helpful, friendly voice assistant.
    Be concise and conversational.
  greeting: "Hello! How can I help you today?"
```

### Tools

```yaml
tools:
  - name: "get_weather"
    description: "Get current weather for a location"
    parameters:
      - name: "location"
        type: "string"
        description: "City name"
        required: true
    # Optional: webhook for external execution
    # webhook_url: "https://api.example.com/weather"
```

### Emotional Intelligence

```yaml
emotion:
  enabled: true
  adaptive_prompts:
    frustrated: "The user seems frustrated. Be extra patient."
    happy: "The user is in a good mood. Match their energy."
    sad: "The user seems sad. Be warm and supportive."
```

## Architecture

```
Frontend (Next.js + Agents UI)
        │ WebRTC
   LiveKit Server (Cloud)
        │
Backend Agent (Python)
   VAD → STT → Emotion → LLM → TTS
```

The system uses LiveKit's WebRTC infrastructure for real-time audio streaming. The Python agent runs as a LiveKit worker that connects to rooms and processes audio through the voice pipeline.

## Project Structure

```
├── agent/                    # Python backend
│   ├── src/
│   │   ├── agent.py          # Main agent (entry point)
│   │   ├── config.py         # YAML config loader
│   │   ├── emotion.py        # Emotional intelligence
│   │   ├── tools.py          # Tool system
│   │   └── hooks.py          # Pipeline lifecycle hooks
│   ├── configs/
│   │   └── default.yaml      # Default configuration
│   ├── tests/                # Pytest test suite
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                 # Next.js frontend
│   ├── app/
│   │   ├── page.tsx          # Main page
│   │   └── api/token/        # Token generation
│   ├── components/
│   │   ├── app/              # App components
│   │   └── ui/               # shadcn/ui components
│   ├── hooks/                # React hooks
│   ├── lib/                  # Utilities & types
│   ├── package.json
│   └── .env.example
│
├── PROGRESS.md               # Development tracking
└── README.md                 # This file
```

## Supported Providers

| Component | Providers |
|-----------|-----------|
| STT | Deepgram (nova-3), OpenAI (whisper) |
| TTS | OpenAI (gpt-4o-mini-tts), ElevenLabs (eleven_turbo_v2_5) |
| LLM | OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-3-5-sonnet) |
| VAD | Silero VAD |
| Turn Detection | LiveKit Multilingual Model |

## Adding New Providers

1. Install the LiveKit plugin: `pip install livekit-plugins-<provider>`
2. Add a new branch in the factory function in `agent/src/agent.py`
3. Update `configs/default.yaml` with the new provider option
4. Update the frontend config panel dropdown options

## Docker Deployment

```bash
# Build the agent
cd agent
docker build -t voice-agent .

# Run
docker run --env-file .env voice-agent
```

For the frontend, deploy to Vercel or any Node.js hosting:

```bash
cd frontend
pnpm build
pnpm start
```

## Testing

```bash
cd agent
pip install -e ".[dev]"
pytest -v --cov=src
```

## Environment Variables

### Backend (agent/.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | LiveKit server URL |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `DEEPGRAM_API_KEY` | If using Deepgram | Deepgram API key |
| `ELEVEN_API_KEY` | If using ElevenLabs | ElevenLabs API key |
| `AGENT_CONFIG` | No | Path to config YAML (default: `configs/default.yaml`) |

### Frontend (frontend/.env.local)

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | LiveKit server URL |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |

## License

MIT
