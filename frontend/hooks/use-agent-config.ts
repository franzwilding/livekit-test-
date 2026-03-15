"use client";

import { useState, useCallback } from "react";
import type { AgentConfig, ToolDefinition } from "@/lib/types";

const DEFAULT_CONFIG: AgentConfig = {
  stt: {
    provider: "deepgram",
    model: "nova-2",
    language: "en",
  },
  tts: {
    provider: "openai",
    model: "tts-1",
    voice: "alloy",
  },
  llm: {
    provider: "openai",
    model: "gpt-4o",
    temperature: 0.7,
  },
  systemPrompt:
    "You are a helpful, friendly AI voice assistant. You speak naturally and conversationally. Keep your responses concise and engaging.",
  greeting:
    "Hello! I'm your AI voice assistant. How can I help you today?",
  emotionEnabled: true,
};

const DEFAULT_TOOLS: ToolDefinition[] = [
  {
    name: "web_search",
    description: "Search the web for current information",
    enabled: true,
  },
  {
    name: "weather",
    description: "Get current weather for a location",
    enabled: true,
  },
  {
    name: "calculator",
    description: "Perform mathematical calculations",
    enabled: false,
  },
  {
    name: "timer",
    description: "Set timers and reminders",
    enabled: false,
  },
];

export function useAgentConfig() {
  const [config, setConfig] = useState<AgentConfig>(DEFAULT_CONFIG);
  const [tools, setTools] = useState<ToolDefinition[]>(DEFAULT_TOOLS);

  const updateSTT = useCallback(
    (updates: Partial<AgentConfig["stt"]>) => {
      setConfig((prev) => ({
        ...prev,
        stt: { ...prev.stt, ...updates },
      }));
    },
    []
  );

  const updateTTS = useCallback(
    (updates: Partial<AgentConfig["tts"]>) => {
      setConfig((prev) => ({
        ...prev,
        tts: { ...prev.tts, ...updates },
      }));
    },
    []
  );

  const updateLLM = useCallback(
    (updates: Partial<AgentConfig["llm"]>) => {
      setConfig((prev) => ({
        ...prev,
        llm: { ...prev.llm, ...updates },
      }));
    },
    []
  );

  const updateSystemPrompt = useCallback((prompt: string) => {
    setConfig((prev) => ({ ...prev, systemPrompt: prompt }));
  }, []);

  const updateGreeting = useCallback((greeting: string) => {
    setConfig((prev) => ({ ...prev, greeting }));
  }, []);

  const toggleEmotion = useCallback(() => {
    setConfig((prev) => ({ ...prev, emotionEnabled: !prev.emotionEnabled }));
  }, []);

  const toggleTool = useCallback((toolName: string) => {
    setTools((prev) =>
      prev.map((tool) =>
        tool.name === toolName ? { ...tool, enabled: !tool.enabled } : tool
      )
    );
  }, []);

  const resetConfig = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
    setTools(DEFAULT_TOOLS);
  }, []);

  return {
    config,
    tools,
    updateSTT,
    updateTTS,
    updateLLM,
    updateSystemPrompt,
    updateGreeting,
    toggleEmotion,
    toggleTool,
    resetConfig,
  };
}
