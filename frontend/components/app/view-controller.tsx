"use client";

import { useState, useCallback } from "react";
import { WelcomeView } from "@/components/app/welcome-view";
import { SessionView } from "@/components/app/session-view";
import { ConfigPanel } from "@/components/app/config-panel";
import { useAgentConfig } from "@/hooks/use-agent-config";
import type { ConnectionDetails, ViewState } from "@/lib/types";

export function ViewController() {
  const [viewState, setViewState] = useState<ViewState>("welcome");
  const [connectionDetails, setConnectionDetails] =
    useState<ConnectionDetails | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);

  const {
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
  } = useAgentConfig();

  const handleConnect = useCallback(async () => {
    setIsConnecting(true);
    try {
      const response = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `Failed to get connection token (${response.status})`
        );
      }

      const details: ConnectionDetails = await response.json();
      setConnectionDetails(details);
      setViewState("session");
    } catch (error) {
      console.error("Failed to connect:", error);
      alert(
        error instanceof Error
          ? error.message
          : "Failed to connect. Please check your configuration."
      );
    } finally {
      setIsConnecting(false);
    }
  }, [config]);

  const handleDisconnect = useCallback(() => {
    setConnectionDetails(null);
    setViewState("welcome");
  }, []);

  return (
    <>
      {viewState === "welcome" && (
        <WelcomeView
          onConnect={handleConnect}
          onOpenConfig={() => setConfigOpen(true)}
          isConnecting={isConnecting}
        />
      )}

      {viewState === "session" && connectionDetails && (
        <SessionView
          connectionDetails={connectionDetails}
          onDisconnect={handleDisconnect}
          onOpenConfig={() => setConfigOpen(true)}
        />
      )}

      <ConfigPanel
        open={configOpen}
        onOpenChange={setConfigOpen}
        config={config}
        tools={tools}
        onUpdateSTT={updateSTT}
        onUpdateTTS={updateTTS}
        onUpdateLLM={updateLLM}
        onUpdateSystemPrompt={updateSystemPrompt}
        onUpdateGreeting={updateGreeting}
        onToggleEmotion={toggleEmotion}
        onToggleTool={toggleTool}
        onReset={resetConfig}
      />
    </>
  );
}
