# AI Voice Agent

Production-ready AI Voice Agent built with [LiveKit Agents SDK](https://docs.livekit.io/agents/) (Python). Designed to be deployed on [LiveKit Cloud](https://cloud.livekit.io) (EU region) and connected from any React/Next.js frontend via WebRTC.

## Features

- **Configurable STT**: Deepgram (nova-3), OpenAI Whisper
- **Configurable TTS**: OpenAI (gpt-4o-mini-tts), ElevenLabs (eleven_turbo_v2_5)
- **Configurable LLM**: OpenAI (GPT-4o), Anthropic (Claude)
- **Turn detection**: LiveKit Multilingual Turn Detector with interruption support (barge-in)
- **Emotional intelligence**: Keyword-based emotion detection with adaptive prompts
- **Tool calling**: Built-in tools (weather, search, reminders) + webhook-based custom tools
- **YAML configuration**: Change models, prompts, and tools without code changes

## Quick Start

### Prerequisites

- Python 3.11+
- [LiveKit Cloud](https://cloud.livekit.io) account (free tier: 1.000 Agent-Minuten/Monat)
- API keys for your chosen providers (OpenAI, Deepgram, etc.)

### 1. Install & configure

```bash
git clone <repo-url>
cd livekit-test-

pip install -e ".[dev]"

cp .env.example .env
# Edit .env with your credentials
```

### 2. Run locally (development)

```bash
# Download VAD + turn detector models
python src/agent.py download-files

# Start in dev mode (connects to LiveKit Cloud)
python src/agent.py dev
```

### 3. Deploy to LiveKit Cloud (EU)

```bash
# Install LiveKit CLI
brew install livekit/tap/lk
# or: curl -sSL https://get.livekit.io/cli | bash

# Login
lk cloud auth login

# Create project in EU
lk cloud project create --name voice-agent --region eu-central

# Set secrets
lk agent secret set OPENAI_API_KEY sk-...
lk agent secret set DEEPGRAM_API_KEY ...
# Optional:
lk agent secret set ANTHROPIC_API_KEY sk-ant-...
lk agent secret set ELEVEN_API_KEY ...

# Deploy
lk agent deploy --region eu-central
```

Done. Your agent is now running in the EU on LiveKit Cloud.

---

## Frontend Integration (React + shadcn/ui)

Connect to this agent from your existing React/Next.js project.

### 1. Install dependencies

```bash
pnpm add livekit-client @livekit/components-react @livekit/components-styles livekit-server-sdk
```

### 2. Install Agents UI components (optional, for beautiful visualizers)

```bash
# Add the agents-ui registry to your components.json:
# "registries": { "@agents-ui": "https://livekit.io/ui/r/{name}.json" }

npx shadcn@latest add @agents-ui/agent-audio-visualizer-bar
npx shadcn@latest add @agents-ui/agent-control-bar
npx shadcn@latest add @agents-ui/agent-chat-transcript
```

### 3. Create token endpoint (PHP)

Your backend needs an endpoint that generates LiveKit access tokens. Install the PHP SDK via Composer:

```bash
composer require agence104/livekit-server-sdk
```

**`/api/livekit-token.php`:**

```php
<?php

require_once __DIR__ . '/../vendor/autoload.php';

use Agence104\LiveKit\AccessToken;
use Agence104\LiveKit\AccessTokenOptions;
use Agence104\LiveKit\VideoGrant;

$apiKey    = getenv('LIVEKIT_API_KEY');
$apiSecret = getenv('LIVEKIT_API_SECRET');
$livekitUrl = getenv('LIVEKIT_URL'); // wss://your-project.livekit.cloud

$participantIdentity = 'user_' . random_int(1000, 9999);
$roomName = 'room_' . random_int(1000, 9999);

$grant = new VideoGrant();
$grant->setRoomJoin(true);
$grant->setRoomName($roomName);
$grant->setCanPublish(true);
$grant->setCanPublishData(true);
$grant->setCanSubscribe(true);

$tokenOptions = (new AccessTokenOptions())
    ->setIdentity($participantIdentity)
    ->setName('User')
    ->setTtl(15 * 60); // 15 minutes

$token = (new AccessToken($apiKey, $apiSecret))
    ->init($tokenOptions)
    ->setGrant($grant)
    ->toJwt();

header('Content-Type: application/json');
header('Cache-Control: no-store');

echo json_encode([
    'serverUrl'        => $livekitUrl,
    'roomName'         => $roomName,
    'participantToken' => $token,
]);
```

The frontend calls this endpoint to get a token before connecting:

### 4. Create the voice agent component

```tsx
import { useState, useCallback } from "react";
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  DisconnectButton,
} from "@livekit/components-react";
import "@livekit/components-styles";

interface ConnectionDetails {
  serverUrl: string;
  roomName: string;
  participantToken: string;
}

// Point this to your PHP backend
const TOKEN_ENDPOINT = "/api/livekit-token.php";

export function VoiceAgent() {
  const [connectionDetails, setConnectionDetails] =
    useState<ConnectionDetails | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const connect = useCallback(async () => {
    setIsConnecting(true);
    try {
      const res = await fetch(TOKEN_ENDPOINT, { method: "POST" });
      const details = await res.json();
      setConnectionDetails(details);
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    setConnectionDetails(null);
  }, []);

  if (!connectionDetails) {
    return (
      <button onClick={connect} disabled={isConnecting}>
        {isConnecting ? "Connecting..." : "Start Conversation"}
      </button>
    );
  }

  return (
    <LiveKitRoom
      token={connectionDetails.participantToken}
      serverUrl={connectionDetails.serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={disconnect}
    >
      <AgentSession />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function AgentSession() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div>
      <p>Agent is: {state}</p>

      {/* Audio visualizer */}
      {audioTrack && (
        <BarVisualizer
          state={state}
          trackRef={audioTrack}
          barCount={32}
          style={{ width: 300, height: 80 }}
        />
      )}

      {/* Disconnect button */}
      <DisconnectButton>End Call</DisconnectButton>
    </div>
  );
}
```

### 5. Use it

```tsx
import { VoiceAgent } from "@/components/voice-agent";

export default function Page() {
  return <VoiceAgent />;
}
```

That's it. The `useVoiceAssistant` hook from `@livekit/components-react` handles all WebRTC audio streaming, transcript events, and agent state tracking automatically.

### Available hooks & components

| Import | Purpose |
|--------|---------|
| `useVoiceAssistant()` | Agent state, audio track, transcript |
| `BarVisualizer` | Animated audio bars |
| `RoomAudioRenderer` | Plays agent audio (required) |
| `DisconnectButton` | End the session |
| `useConnectionState()` | Connection status |
| `useTracks()` | Access local/remote audio tracks |

For the full Agents UI component library (visualizers, control bar, chat transcript), see [livekit.io/ui](https://livekit.io/ui).

---

## Configuration

All agent behavior is configured via `configs/default.yaml`:

### Models

```yaml
stt:
  provider: "deepgram"    # or "openai"
  model: "nova-3"
  language: "multi"

tts:
  provider: "openai"      # or "elevenlabs"
  model: "gpt-4o-mini-tts"
  voice: "coral"

llm:
  provider: "openai"      # or "anthropic"
  model: "gpt-4o"
  temperature: 0.7
```

### System Prompt & Greeting

```yaml
agent:
  name: "Voice Assistant"
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
    # Optional webhook for external execution:
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

## Client Messaging (Agent → Frontend)

The agent can send structured data messages to the frontend during a session via LiveKit's data channel. This is similar to ElevenLabs' "Client Tools" — use it to push RAG results, status updates, tool outputs, or any custom data to the UI.

### Agent-side (Python)

The `ClientMessenger` is available on every `VoiceAssistant` instance via `self.messenger`:

```python
# Inside a @function_tool or any agent method:

# Send RAG results with relevance scores
await self.messenger.send_rag_result(
    query="company vacation policy",
    chunks=[
        {"text": "Employees get 30 days...", "score": 0.95, "source": "hr.pdf"},
        {"text": "Remote work policy...", "score": 0.62, "source": "handbook.pdf"},
    ],
    relevance=0.87,
)

# Send status / progress updates
await self.messenger.send_status("searching", progress=0.5)

# Send any custom message type
await self.messenger.send("custom_event", {
    "whatever": "you need",
    "nested": {"data": True},
})

# Send only to a specific participant
await self.messenger.send("private_data", {"x": 1},
    destination_identities=["user_42"])

# Use LOSSY mode for high-frequency updates (no delivery guarantee)
from src.messaging import DeliveryMode
await self.messenger.send("live_indicator", {"level": 0.8},
    mode=DeliveryMode.LOSSY)
```

Available convenience methods:
| Method | Message type | Use case |
|--------|-------------|----------|
| `send(type, payload)` | any | Generic — send anything |
| `send_rag_result(query, chunks, relevance)` | `rag_result` | RAG retrieval results |
| `send_status(stage, progress, detail)` | `status` | Progress / stage updates |
| `send_tool_result(tool_name, result)` | `tool_result` | Tool output for UI display |
| `send_error(code, message)` | `error` | Error notifications |

### Frontend-side (React/TypeScript)

All messages arrive on the LiveKit room's data channel with topic `"agent:message"`. Use the `@livekit/components-react` hook to listen:

```tsx
import { useDataChannel } from "@livekit/components-react";
import { useCallback, useState } from "react";

interface AgentMessage {
  type: string;
  payload: Record<string, any>;
  timestamp: number;
}

function useAgentMessages() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);

  const onMessage = useCallback((msg: { payload: Uint8Array; topic?: string }) => {
    if (msg.topic !== "agent:message") return;
    const parsed: AgentMessage = JSON.parse(
      new TextDecoder().decode(msg.payload)
    );
    setMessages((prev) => [...prev, parsed]);
  }, []);

  useDataChannel("agent:message", onMessage);

  return messages;
}
```

Then use it in your component:

```tsx
function AgentSession() {
  const { state, audioTrack } = useVoiceAssistant();
  const messages = useAgentMessages();

  // Filter by type
  const ragResults = messages.filter((m) => m.type === "rag_result");
  const latestStatus = messages.findLast((m) => m.type === "status");

  return (
    <div>
      {/* Show RAG relevance */}
      {ragResults.map((r, i) => (
        <div key={i}>
          <span>Query: {r.payload.query}</span>
          <span>Relevance: {(r.payload.relevance * 100).toFixed(0)}%</span>
          {r.payload.chunks.map((chunk: any, j: number) => (
            <p key={j}>{chunk.text} (score: {chunk.score})</p>
          ))}
        </div>
      ))}

      {/* Show status */}
      {latestStatus && <p>Agent: {latestStatus.payload.stage}</p>}
    </div>
  );
}
```

### Wire format

Every message is a JSON object on topic `"agent:message"`:

```json
{
  "type": "rag_result",
  "payload": {
    "query": "vacation policy",
    "chunks": [{"text": "...", "score": 0.95}],
    "relevance": 0.87
  },
  "timestamp": 1710500000.123
}
```

## Project Structure

```
├── src/
│   ├── agent.py       # Main agent entry point (VoiceAssistant class)
│   ├── config.py      # YAML config loader (dataclasses)
│   ├── messaging.py   # Client messaging layer (agent → frontend data channel)
│   ├── emotion.py     # Emotion detection + adaptive prompts
│   ├── tools.py       # Built-in tools + webhook support
│   └── hooks.py       # Pipeline lifecycle hooks
├── configs/
│   └── default.yaml   # Agent configuration
├── tests/             # Pytest test suite
├── pyproject.toml     # Dependencies
├── Dockerfile         # Container for deployment
├── .env.example       # Environment template
└── README.md
```

## Supported Providers

| Component | Providers |
|-----------|-----------|
| STT | Deepgram (nova-3), OpenAI (whisper) |
| TTS | OpenAI (gpt-4o-mini-tts), ElevenLabs (eleven_turbo_v2_5) |
| LLM | OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-sonnet) |
| VAD | Silero VAD |
| Turn Detection | LiveKit Multilingual Model |

## Adding New Providers

1. Install the LiveKit plugin: `pip install livekit-plugins-<provider>`
2. Add a new branch in the factory function in `src/agent.py`
3. Update `configs/default.yaml` with the new provider option

## Testing

```bash
pip install -e ".[dev]"
pytest -v --cov=src
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | LiveKit Cloud URL (`wss://...livekit.cloud`) |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `DEEPGRAM_API_KEY` | If using Deepgram | Deepgram API key |
| `ELEVEN_API_KEY` | If using ElevenLabs | ElevenLabs API key |
| `AGENT_CONFIG` | No | Config path (default: `configs/default.yaml`) |

## License

MIT
