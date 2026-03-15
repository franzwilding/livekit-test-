"use client";

import { useState } from "react";
import { Mic, Settings, Sparkles, Zap, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface WelcomeViewProps {
  onConnect: () => void;
  onOpenConfig: () => void;
  isConnecting: boolean;
}

export function WelcomeView({
  onConnect,
  onOpenConfig,
  isConnecting,
}: WelcomeViewProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-pink-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 flex flex-col items-center max-w-2xl mx-auto text-center animate-in">
        {/* Logo */}
        <div className="relative mb-8">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-500/25">
            <Mic className="w-10 h-10 text-white" />
          </div>
          <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 opacity-20 blur-lg" />
        </div>

        {/* Title */}
        <h1 className="text-5xl font-bold tracking-tight mb-4">
          <span className="gradient-text">AI Voice Agent</span>
        </h1>

        <p className="text-lg text-muted-foreground mb-8 max-w-md leading-relaxed">
          Experience natural conversations powered by advanced AI. Speak
          freely and get intelligent, real-time responses.
        </p>

        {/* Feature badges */}
        <div className="flex flex-wrap gap-2 justify-center mb-10">
          <Badge variant="info" className="gap-1.5 py-1 px-3">
            <Sparkles className="w-3 h-3" />
            Emotion Aware
          </Badge>
          <Badge variant="success" className="gap-1.5 py-1 px-3">
            <Zap className="w-3 h-3" />
            Low Latency
          </Badge>
          <Badge variant="warning" className="gap-1.5 py-1 px-3">
            <Shield className="w-3 h-3" />
            Private & Secure
          </Badge>
        </div>

        {/* Connect button */}
        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <Button
            variant="gradient"
            size="xl"
            onClick={onConnect}
            disabled={isConnecting}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="relative group min-w-[200px]"
          >
            {isConnecting ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Mic
                  className={`w-5 h-5 transition-transform duration-300 ${
                    isHovered ? "scale-110" : ""
                  }`}
                />
                Start Conversation
              </>
            )}
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={onOpenConfig}
            className="glass glass-hover"
          >
            <Settings className="w-4 h-4" />
            Configure
          </Button>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16 w-full">
          <FeatureCard
            icon={<Mic className="w-5 h-5 text-blue-400" />}
            title="Voice First"
            description="Natural speech recognition and synthesis with multiple provider options"
          />
          <FeatureCard
            icon={<Sparkles className="w-5 h-5 text-purple-400" />}
            title="Intelligent"
            description="Powered by leading LLMs with configurable prompts and behaviors"
          />
          <FeatureCard
            icon={<Zap className="w-5 h-5 text-pink-400" />}
            title="Real-time"
            description="Ultra-low latency streaming with LiveKit infrastructure"
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="glass rounded-xl p-5 text-left glass-hover group cursor-default">
      <div className="mb-3 p-2 w-fit rounded-lg bg-white/5 group-hover:bg-white/10 transition-colors">
        {icon}
      </div>
      <h3 className="font-semibold text-sm mb-1">{title}</h3>
      <p className="text-xs text-muted-foreground leading-relaxed">
        {description}
      </p>
    </div>
  );
}
