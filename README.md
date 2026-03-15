# AI Voice Agent

AI Voice Agent built with [LiveKit Agents SDK](https://docs.livekit.io/agents/) (Python). Deploys on [LiveKit Cloud](https://cloud.livekit.io) (EU region), connects from any frontend via WebRTC.

## Features

- **STT**: Deepgram (nova-3)
- **TTS**: OpenAI (gpt-4o-mini-tts)
- **LLM**: OpenAI (GPT-4o)
- **Turn detection**: LiveKit Multilingual Turn Detector with interruption support (barge-in)
- **Client messaging**: Send structured data (RAG results, status, etc.) to the frontend via data channel
- **Tool calling**: Built-in tools (weather, search, reminders) + webhook support

## Quick Start

### Prerequisites

- Python 3.11+
- [LiveKit Cloud](https://cloud.livekit.io) account
- API keys (OpenAI, Deepgram)

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
python src/agent.py download-files
python src/agent.py dev
```

### 3. Deploy to LiveKit Cloud (EU)

```bash
brew install livekit/tap/lk  # or: curl -sSL https://get.livekit.io/cli | bash

lk cloud auth login
lk cloud project create --name voice-agent --region eu-central

lk agent secret set OPENAI_API_KEY sk-...
lk agent secret set DEEPGRAM_API_KEY ...

lk agent deploy --region eu-central
```

---

## Frontend Integration

Connect to this agent from your existing React project.

### 1. Install dependencies

```bash
pnpm add livekit-client @livekit/components-react @livekit/components-styles
```

### 2. Create a token endpoint on your backend

Your backend needs a POST endpoint that generates a LiveKit access token (JWT signed with your LiveKit API secret).

**Request:** `POST /api/livekit-token` (no body required)

**Response:** `application/json`

```json
{
  "serverUrl": "wss://your-project.livekit.cloud",
  "roomName": "room_4821",
  "participantToken": "<JWT>"
}
```

**JWT payload** (sign with HS256 using `LIVEKIT_API_SECRET`):

```json
{
  "iss": "<LIVEKIT_API_KEY>",
  "sub": "user_1234",
  "name": "User",
  "exp": "<now + 900>",
  "nbf": "<now>",
  "video": {
    "room": "room_4821",
    "roomJoin": true,
    "canPublish": true,
    "canPublishData": true,
    "canSubscribe": true
  }
}
```

| Field | Description |
|-------|-------------|
| `iss` | Your `LIVEKIT_API_KEY` |
| `sub` | Unique participant identity (e.g. user ID) |
| `exp` | Expiry (e.g. 15 minutes from now) |
| `video.room` | Room name (generate a random one per session) |
| `video.canPublishData` | Must be `true` for `ClientMessenger` data channel |

LiveKit server SDKs (optional higher-level API): PHP (`agence104/livekit-server-sdk`), Python (`livekit-server-sdk`), Node (`livekit-server-sdk`), see [docs.livekit.io/server/generating-tokens](https://docs.livekit.io/server/generating-tokens/).

### 3. Create the voice agent component

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

const TOKEN_ENDPOINT = "/api/livekit-token";

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
      {audioTrack && (
        <BarVisualizer
          state={state}
          trackRef={audioTrack}
          barCount={32}
          style={{ width: 300, height: 80 }}
        />
      )}
      <DisconnectButton>End Call</DisconnectButton>
    </div>
  );
}
```

---

## Client Messaging (Agent → Frontend)

Send structured data from the agent to the frontend during a session via LiveKit's data channel. Use it for RAG results, status updates, tool outputs, or any custom data.

### Agent-side (Python)

```python
# Inside a @function_tool or any agent method:

# RAG results with relevance scores
await self.messenger.send_rag_result(
    query="company vacation policy",
    chunks=[
        {"text": "Employees get 30 days...", "score": 0.95, "source": "hr.pdf"},
        {"text": "Remote work policy...", "score": 0.62, "source": "handbook.pdf"},
    ],
    relevance=0.87,
)

# Status / progress updates
await self.messenger.send_status("searching", progress=0.5)

# Any custom message
await self.messenger.send("custom_event", {"whatever": "you need"})
```

| Method | Message type | Use case |
|--------|-------------|----------|
| `send(type, payload)` | any | Generic — send anything |
| `send_rag_result(query, chunks, relevance)` | `rag_result` | RAG retrieval results |
| `send_status(stage, progress, detail)` | `status` | Progress / stage updates |
| `send_tool_result(tool_name, result)` | `tool_result` | Tool output for UI display |
| `send_error(code, message)` | `error` | Error notifications |

### Frontend-side (React/TypeScript)

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

### Wire format

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

---

## Project Structure

```
├── src/
│   ├── agent.py       # Agent entry point + VoiceAssistant + tools
│   └── messaging.py   # Client messaging (agent → frontend data channel)
├── tests/
├── .github/workflows/ # CI (pytest on every push)
├── pyproject.toml
├── Dockerfile
├── .env.example
└── README.md
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v --cov=src
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | `wss://...livekit.cloud` |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `DEEPGRAM_API_KEY` | Yes | Deepgram API key |

## License

MIT
