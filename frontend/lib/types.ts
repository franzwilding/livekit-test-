export interface ConnectionDetails {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
}

export type AgentState = "idle" | "listening" | "thinking" | "speaking";

export interface TranscriptEntry {
  speaker: "user" | "agent";
  text: string;
  timestamp: number;
  emotion?: string;
}

export interface STTConfig {
  provider: string;
  model: string;
  language: string;
}

export interface TTSConfig {
  provider: string;
  model: string;
  voice: string;
}

export interface LLMConfig {
  provider: string;
  model: string;
  temperature: number;
}

export interface AgentConfig {
  stt: STTConfig;
  tts: TTSConfig;
  llm: LLMConfig;
  systemPrompt: string;
  greeting: string;
  emotionEnabled: boolean;
}

export type ViewState = "welcome" | "session";

export interface ToolDefinition {
  name: string;
  description: string;
  enabled: boolean;
}
