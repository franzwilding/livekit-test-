# AI Voice Agent — Progress Tracking

## Project Overview
Production-ready AI Voice Agent built with LiveKit Agents SDK (Python backend) and LiveKit Agents UI (Next.js frontend). Supports configurable STT, TTS, LLM providers, emotional intelligence, turn detection, interruption handling, and tool calling.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                     │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Welcome  │  │  Session     │  │  Config Panel     │  │
│  │ View     │──│  View        │  │  (Models/Prompts) │  │
│  │          │  │  - Visualizer│  │  - STT Provider   │  │
│  │ Connect  │  │  - Transcript│  │  - TTS Provider   │  │
│  │ Button   │  │  - Controls  │  │  - LLM Provider   │  │
│  └──────────┘  │  - Emotion   │  │  - System Prompt  │  │
│                └──────┬───────┘  │  - Tools          │  │
│                       │          └───────────────────┘  │
│              LiveKit Client SDK                          │
└───────────────────────┬─────────────────────────────────┘
                        │ WebRTC
┌───────────────────────┴─────────────────────────────────┐
│                  LiveKit Server (Cloud)                   │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│               Backend Agent (Python)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────┐  │
│  │  VAD    │  │  STT    │  │  LLM    │  │   TTS     │  │
│  │ Silero  │  │Deepgram │  │ OpenAI  │  │ OpenAI    │  │
│  │         │  │ OpenAI  │  │Anthropic│  │ElevenLabs │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬──────┘  │
│       │            │            │             │          │
│  ┌────┴────────────┴────────────┴─────────────┴──────┐  │
│  │              Voice Pipeline                        │  │
│  │  Audio → VAD → STT → Emotion → LLM → TTS → Audio │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Turn Detect. │  │  Emotion     │  │   Tools      │  │
│  │ Multilingual │  │  Intelligence│  │  Function    │  │
│  │ Interruption │  │  Adaptive    │  │  Calling     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend (Python)
- **Framework**: LiveKit Agents SDK v1.4
- **VAD**: Silero VAD (prewarmed)
- **STT**: Deepgram (nova-3), OpenAI Whisper
- **LLM**: OpenAI (GPT-4o), Anthropic (Claude)
- **TTS**: OpenAI (gpt-4o-mini-tts), ElevenLabs (eleven_turbo_v2_5)
- **Turn Detection**: LiveKit Multilingual Turn Detector
- **Config**: YAML-based configuration system

### Frontend (Next.js)
- **Framework**: Next.js 15 with React 19
- **UI**: shadcn/ui + LiveKit Agents UI components
- **Styling**: Tailwind CSS with dark theme
- **LiveKit**: @livekit/components-react, livekit-client
- **State**: React hooks for config management

## Features

### Core Voice Pipeline
- [x] Real-time audio streaming via WebRTC (LiveKit)
- [x] Voice Activity Detection (Silero VAD)
- [x] Configurable STT (Deepgram, OpenAI)
- [x] Configurable LLM (OpenAI, Anthropic)
- [x] Configurable TTS (OpenAI, ElevenLabs)
- [x] Turn detection (multilingual)
- [x] Interruption handling (barge-in)

### Emotional Intelligence
- [x] Keyword-based emotion detection
- [x] Emotion state tracking with rolling window
- [x] Adaptive system prompts based on detected emotion
- [x] Configurable emotion-response mappings

### Tool Calling
- [x] Built-in tools (weather, search, reminder)
- [x] YAML-configurable tool definitions
- [x] Webhook support for external tool execution
- [x] Dynamic tool registration

### Frontend UI
- [x] Beautiful dark-theme interface
- [x] Audio visualizer (animated bars)
- [x] Real-time conversation transcript
- [x] Agent state indicators (listening, thinking, speaking)
- [x] Configuration panel (models, prompts, tools)
- [x] Connection management (connect/disconnect)

### Configuration System
- [x] YAML-based configuration (`configs/default.yaml`)
- [x] Environment variable support
- [x] Runtime model switching via config panel
- [x] Configurable system prompts
- [x] Configurable greeting messages

### Production Readiness
- [x] Docker support
- [x] Comprehensive test suite
- [x] Error handling throughout
- [x] Logging
- [x] Environment-based configuration

## Task Status

| Task | Status | Notes |
|------|--------|-------|
| Project architecture design | DONE | LiveKit-based architecture |
| Backend: Agent core | DONE | LiveKit Agents SDK v1.4 |
| Backend: Config system (YAML) | DONE | Full config parsing |
| Backend: STT factory (Deepgram/OpenAI) | DONE | Provider switching |
| Backend: TTS factory (OpenAI/ElevenLabs) | DONE | Provider switching |
| Backend: LLM factory (OpenAI/Anthropic) | DONE | Provider switching |
| Backend: Emotion detection | DONE | Keyword + rolling window |
| Backend: Tool system | DONE | Built-in + webhook |
| Backend: Turn detection | DONE | Multilingual model |
| Backend: Tests | DONE | Config, emotion, tools, agent |
| Backend: Dockerfile | DONE | Production-ready |
| Frontend: Next.js setup | DONE | Next.js 15, React 19 |
| Frontend: shadcn/ui components | DONE | Full component library |
| Frontend: Token generation API | DONE | JWT token endpoint |
| Frontend: Welcome view | DONE | Connect button |
| Frontend: Session view | DONE | Visualizer + transcript |
| Frontend: Config panel | DONE | Full model/prompt config |
| Frontend: Dark theme styling | DONE | Glass-morphism, animations |
| Documentation: README | DONE | Full setup guide |
| Documentation: PROGRESS.md | DONE | This file |

## How to Continue

If you're an agent picking up this work:

1. **To modify the voice pipeline**: Edit `agent/src/agent.py` — the `VoiceAssistant` class and `voice_agent_session` function
2. **To add new STT/TTS/LLM providers**: Add new branches in the factory functions in `agent/src/agent.py` and install the corresponding `livekit-plugins-*` package
3. **To add new tools**: Either add to `agent/configs/default.yaml` or implement new `@function_tool` methods on the `VoiceAssistant` class
4. **To modify emotion detection**: Edit `agent/src/emotion.py` — add keywords or implement ML-based detection
5. **To modify the UI**: Edit components in `frontend/components/app/`
6. **To add new UI components**: Use `npx shadcn@latest add @agents-ui/{component-name}`

## Environment Variables Required

### Backend (agent/.env)
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
OPENAI_API_KEY=sk-...        # If using OpenAI STT/TTS/LLM
ANTHROPIC_API_KEY=sk-ant-... # If using Anthropic LLM
DEEPGRAM_API_KEY=...         # If using Deepgram STT
ELEVEN_API_KEY=...           # If using ElevenLabs TTS
```

### Frontend (frontend/.env.local)
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```
