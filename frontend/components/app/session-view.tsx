"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  DisconnectButton,
  useConnectionState,
  useTracks,
} from "@livekit/components-react";
import { ConnectionState, Track } from "livekit-client";
import {
  Mic,
  MicOff,
  PhoneOff,
  Settings,
  Clock,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { ConnectionDetails, TranscriptEntry, AgentState } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

interface SessionViewProps {
  connectionDetails: ConnectionDetails;
  onDisconnect: () => void;
  onOpenConfig: () => void;
}

export function SessionView({
  connectionDetails,
  onDisconnect,
  onOpenConfig,
}: SessionViewProps) {
  return (
    <LiveKitRoom
      token={connectionDetails.participantToken}
      serverUrl={connectionDetails.serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={onDisconnect}
      className="flex flex-col h-screen"
    >
      <SessionContent onDisconnect={onDisconnect} onOpenConfig={onOpenConfig} />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function SessionContent({
  onDisconnect,
  onOpenConfig,
}: {
  onDisconnect: () => void;
  onOpenConfig: () => void;
}) {
  const voiceAssistant = useVoiceAssistant();
  const connectionState = useConnectionState();
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [sessionDuration, setSessionDuration] = useState(0);
  const [showTranscript, setShowTranscript] = useState(true);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const localTracks = useTracks([Track.Source.Microphone]);

  // Session timer
  useEffect(() => {
    if (connectionState !== ConnectionState.Connected) return;
    const interval = setInterval(() => {
      setSessionDuration((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [connectionState]);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  // Track agent state for transcript updates
  useEffect(() => {
    const agentState = voiceAssistant.state;
    if (agentState === "speaking" && voiceAssistant.audioTrack) {
      // The voice assistant is speaking, transcript will be updated via data messages
    }
  }, [voiceAssistant.state, voiceAssistant.audioTrack]);

  // Handle mute toggle
  const toggleMute = useCallback(() => {
    const localTrack = localTracks.find(
      (t) => t.source === Track.Source.Microphone
    );
    if (localTrack?.publication?.track) {
      if (isMuted) {
        localTrack.publication.track.unmute();
      } else {
        localTrack.publication.track.mute();
      }
      setIsMuted(!isMuted);
    }
  }, [isMuted, localTracks]);

  const agentState: AgentState = (voiceAssistant.state as AgentState) || "idle";

  const getStateColor = (state: AgentState) => {
    switch (state) {
      case "listening":
        return "bg-blue-500";
      case "thinking":
        return "bg-amber-500";
      case "speaking":
        return "bg-emerald-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStateLabel = (state: AgentState) => {
    switch (state) {
      case "listening":
        return "Listening";
      case "thinking":
        return "Thinking";
      case "speaking":
        return "Speaking";
      default:
        return "Idle";
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className={`w-2.5 h-2.5 rounded-full ${getStateColor(
                agentState
              )} ${agentState !== "idle" ? "state-pulse" : ""}`}
            />
            <span className="text-sm font-medium text-foreground">
              {getStateLabel(agentState)}
            </span>
          </div>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span className="text-xs font-mono">
              {formatDuration(sessionDuration)}
            </span>
          </div>
          {connectionState === ConnectionState.Connected && (
            <Badge variant="success" className="text-xs">
              Connected
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowTranscript(!showTranscript)}
            className="text-muted-foreground hover:text-foreground"
          >
            <MessageSquare className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onOpenConfig}
            className="text-muted-foreground hover:text-foreground"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Visualizer area */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 relative">
          {/* Background glow */}
          <div
            className={`absolute inset-0 transition-opacity duration-1000 ${
              agentState === "speaking" ? "opacity-100" : "opacity-0"
            }`}
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-3xl" />
          </div>
          <div
            className={`absolute inset-0 transition-opacity duration-1000 ${
              agentState === "listening" ? "opacity-100" : "opacity-0"
            }`}
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-blue-500/10 rounded-full blur-3xl" />
          </div>

          {/* Agent avatar and visualizer */}
          <div className="relative z-10 flex flex-col items-center gap-8">
            {/* Avatar ring */}
            <div
              className={`relative w-32 h-32 rounded-full flex items-center justify-center ${
                agentState !== "idle"
                  ? "ring-2 ring-offset-4 ring-offset-[#0a0a0a]"
                  : ""
              } ${
                agentState === "listening"
                  ? "ring-blue-500"
                  : agentState === "thinking"
                  ? "ring-amber-500"
                  : agentState === "speaking"
                  ? "ring-emerald-500"
                  : ""
              } transition-all duration-500`}
            >
              <div className="w-full h-full rounded-full bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 glass flex items-center justify-center">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center">
                  {agentState === "thinking" ? (
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0ms]" />
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:150ms]" />
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:300ms]" />
                    </div>
                  ) : (
                    <Mic className="w-10 h-10 text-white" />
                  )}
                </div>
              </div>
              {agentState !== "idle" && (
                <div className="absolute inset-0 rounded-full animate-pulse-glow bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 -z-10" />
              )}
            </div>

            {/* Bar visualizer */}
            <div className="w-80 h-24">
              {voiceAssistant.audioTrack ? (
                <BarVisualizer
                  state={voiceAssistant.state}
                  trackRef={voiceAssistant.audioTrack}
                  barCount={48}
                  options={{
                    minHeight: 4,
                  }}
                  className="w-full h-full"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <div className="flex gap-1 items-end h-12">
                    {Array.from({ length: 48 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-white/10 rounded-full transition-all duration-300"
                        style={{
                          height: `${Math.max(
                            4,
                            Math.sin(i * 0.3) * 20 + 20
                          )}%`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* State text */}
            <p className="text-sm text-muted-foreground">
              {agentState === "idle" && "Ready to listen"}
              {agentState === "listening" && "Listening to you..."}
              {agentState === "thinking" && "Processing your request..."}
              {agentState === "speaking" && "Speaking..."}
            </p>
          </div>
        </div>

        {/* Transcript panel */}
        {showTranscript && (
          <div className="w-full lg:w-96 border-t lg:border-t-0 lg:border-l border-white/5 flex flex-col bg-black/20">
            <div className="px-4 py-3 border-b border-white/5">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-muted-foreground" />
                Transcript
              </h3>
            </div>
            <ScrollArea className="flex-1 p-4">
              {transcripts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-center">
                  <MessageSquare className="w-8 h-8 text-muted-foreground/50 mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Start speaking to see the transcript
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {transcripts.map((entry, index) => (
                    <TranscriptBubble key={index} entry={entry} />
                  ))}
                </div>
              )}
              <div ref={transcriptEndRef} />
            </ScrollArea>
          </div>
        )}
      </div>

      {/* Control bar */}
      <div className="flex items-center justify-center gap-4 px-6 py-5 border-t border-white/5">
        <Button
          variant={isMuted ? "destructive" : "outline"}
          size="icon"
          onClick={toggleMute}
          className={`w-12 h-12 rounded-full transition-all duration-300 ${
            isMuted
              ? "bg-red-500/20 border-red-500/50 text-red-400 hover:bg-red-500/30"
              : "glass glass-hover"
          }`}
        >
          {isMuted ? (
            <MicOff className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </Button>

        <DisconnectButton className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-all duration-300 hover:scale-105 shadow-lg shadow-red-500/25">
          <PhoneOff className="w-6 h-6" />
        </DisconnectButton>

        <Button
          variant="outline"
          size="icon"
          onClick={onOpenConfig}
          className="w-12 h-12 rounded-full glass glass-hover"
        >
          <Settings className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}

function TranscriptBubble({ entry }: { entry: TranscriptEntry }) {
  const isAgent = entry.speaker === "agent";

  return (
    <div
      className={`flex flex-col gap-1 animate-in ${
        isAgent ? "items-start" : "items-end"
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground font-medium">
          {isAgent ? "Agent" : "You"}
        </span>
        {entry.emotion && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
            {entry.emotion}
          </Badge>
        )}
        <span className="text-[10px] text-muted-foreground/50">
          {formatTimestamp(entry.timestamp)}
        </span>
      </div>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isAgent
            ? "bg-white/5 border border-white/10 rounded-tl-sm"
            : "bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/20 rounded-tr-sm"
        }`}
      >
        {entry.text}
      </div>
    </div>
  );
}
