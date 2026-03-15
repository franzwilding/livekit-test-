"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Mic,
  Volume2,
  Brain,
  MessageSquare,
  Wrench,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import type { AgentConfig, ToolDefinition } from "@/lib/types";

interface ConfigPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: AgentConfig;
  tools: ToolDefinition[];
  onUpdateSTT: (updates: Partial<AgentConfig["stt"]>) => void;
  onUpdateTTS: (updates: Partial<AgentConfig["tts"]>) => void;
  onUpdateLLM: (updates: Partial<AgentConfig["llm"]>) => void;
  onUpdateSystemPrompt: (prompt: string) => void;
  onUpdateGreeting: (greeting: string) => void;
  onToggleEmotion: () => void;
  onToggleTool: (toolName: string) => void;
  onReset: () => void;
}

const STT_PROVIDERS = [
  {
    value: "deepgram",
    label: "Deepgram",
    models: ["nova-2", "nova-2-general", "nova-2-meeting", "nova-2-phonecall"],
  },
  {
    value: "openai",
    label: "OpenAI",
    models: ["whisper-1"],
  },
];

const TTS_PROVIDERS = [
  {
    value: "openai",
    label: "OpenAI",
    models: ["tts-1", "tts-1-hd"],
    voices: ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
  },
  {
    value: "elevenlabs",
    label: "ElevenLabs",
    models: ["eleven_turbo_v2", "eleven_multilingual_v2"],
    voices: ["rachel", "drew", "clyde", "paul", "domi", "dave", "fin"],
  },
];

const LLM_PROVIDERS = [
  {
    value: "openai",
    label: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  },
  {
    value: "anthropic",
    label: "Anthropic",
    models: ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
  },
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "zh", label: "Chinese" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "nl", label: "Dutch" },
];

export function ConfigPanel({
  open,
  onOpenChange,
  config,
  tools,
  onUpdateSTT,
  onUpdateTTS,
  onUpdateLLM,
  onUpdateSystemPrompt,
  onUpdateGreeting,
  onToggleEmotion,
  onToggleTool,
  onReset,
}: ConfigPanelProps) {
  const currentSTTProvider = STT_PROVIDERS.find(
    (p) => p.value === config.stt.provider
  );
  const currentTTSProvider = TTS_PROVIDERS.find(
    (p) => p.value === config.tts.provider
  );
  const currentLLMProvider = LLM_PROVIDERS.find(
    (p) => p.value === config.llm.provider
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md bg-[#0a0a0a] border-white/10 p-0"
      >
        <SheetHeader className="px-6 pt-6 pb-4">
          <SheetTitle className="gradient-text text-xl">
            Agent Configuration
          </SheetTitle>
          <SheetDescription>
            Customize the voice agent&apos;s behavior and capabilities.
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-140px)]">
          <div className="px-6 pb-6">
            <Tabs defaultValue="voice" className="w-full">
              <TabsList className="w-full grid grid-cols-4 mb-6">
                <TabsTrigger value="voice" className="text-xs gap-1">
                  <Mic className="w-3 h-3" />
                  Voice
                </TabsTrigger>
                <TabsTrigger value="llm" className="text-xs gap-1">
                  <Brain className="w-3 h-3" />
                  LLM
                </TabsTrigger>
                <TabsTrigger value="prompt" className="text-xs gap-1">
                  <MessageSquare className="w-3 h-3" />
                  Prompt
                </TabsTrigger>
                <TabsTrigger value="tools" className="text-xs gap-1">
                  <Wrench className="w-3 h-3" />
                  Tools
                </TabsTrigger>
              </TabsList>

              {/* Voice Tab (STT + TTS) */}
              <TabsContent value="voice" className="space-y-6">
                {/* STT Section */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Mic className="w-4 h-4 text-blue-400" />
                    <h4 className="text-sm font-semibold">
                      Speech-to-Text (STT)
                    </h4>
                  </div>

                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Provider
                      </Label>
                      <Select
                        value={config.stt.provider}
                        onValueChange={(value) => {
                          const provider = STT_PROVIDERS.find(
                            (p) => p.value === value
                          );
                          onUpdateSTT({
                            provider: value,
                            model: provider?.models[0] || "",
                          });
                        }}
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {STT_PROVIDERS.map((provider) => (
                            <SelectItem
                              key={provider.value}
                              value={provider.value}
                            >
                              {provider.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Model
                      </Label>
                      <Select
                        value={config.stt.model}
                        onValueChange={(value) =>
                          onUpdateSTT({ model: value })
                        }
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {currentSTTProvider?.models.map((model) => (
                            <SelectItem key={model} value={model}>
                              {model}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Language
                      </Label>
                      <Select
                        value={config.stt.language}
                        onValueChange={(value) =>
                          onUpdateSTT({ language: value })
                        }
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {LANGUAGES.map((lang) => (
                            <SelectItem key={lang.value} value={lang.value}>
                              {lang.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <Separator className="bg-white/5" />

                {/* TTS Section */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Volume2 className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-semibold">
                      Text-to-Speech (TTS)
                    </h4>
                  </div>

                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Provider
                      </Label>
                      <Select
                        value={config.tts.provider}
                        onValueChange={(value) => {
                          const provider = TTS_PROVIDERS.find(
                            (p) => p.value === value
                          );
                          onUpdateTTS({
                            provider: value,
                            model: provider?.models[0] || "",
                            voice: provider?.voices[0] || "",
                          });
                        }}
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TTS_PROVIDERS.map((provider) => (
                            <SelectItem
                              key={provider.value}
                              value={provider.value}
                            >
                              {provider.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Model
                      </Label>
                      <Select
                        value={config.tts.model}
                        onValueChange={(value) =>
                          onUpdateTTS({ model: value })
                        }
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {currentTTSProvider?.models.map((model) => (
                            <SelectItem key={model} value={model}>
                              {model}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Voice
                      </Label>
                      <Select
                        value={config.tts.voice}
                        onValueChange={(value) =>
                          onUpdateTTS({ voice: value })
                        }
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {currentTTSProvider?.voices.map((voice) => (
                            <SelectItem key={voice} value={voice}>
                              {voice.charAt(0).toUpperCase() + voice.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* LLM Tab */}
              <TabsContent value="llm" className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-emerald-400" />
                    <h4 className="text-sm font-semibold">
                      Language Model (LLM)
                    </h4>
                  </div>

                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Provider
                      </Label>
                      <Select
                        value={config.llm.provider}
                        onValueChange={(value) => {
                          const provider = LLM_PROVIDERS.find(
                            (p) => p.value === value
                          );
                          onUpdateLLM({
                            provider: value,
                            model: provider?.models[0] || "",
                          });
                        }}
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {LLM_PROVIDERS.map((provider) => (
                            <SelectItem
                              key={provider.value}
                              value={provider.value}
                            >
                              {provider.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Model
                      </Label>
                      <Select
                        value={config.llm.model}
                        onValueChange={(value) =>
                          onUpdateLLM({ model: value })
                        }
                      >
                        <SelectTrigger className="glass">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {currentLLMProvider?.models.map((model) => (
                            <SelectItem key={model} value={model}>
                              {model}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-xs text-muted-foreground">
                          Temperature
                        </Label>
                        <span className="text-xs font-mono text-muted-foreground">
                          {config.llm.temperature.toFixed(1)}
                        </span>
                      </div>
                      <Slider
                        value={[config.llm.temperature]}
                        min={0}
                        max={2}
                        step={0.1}
                        onValueChange={([value]) =>
                          onUpdateLLM({ temperature: value })
                        }
                        className="w-full"
                      />
                      <div className="flex justify-between text-[10px] text-muted-foreground/50">
                        <span>Precise</span>
                        <span>Creative</span>
                      </div>
                    </div>
                  </div>
                </div>

                <Separator className="bg-white/5" />

                {/* Emotion Intelligence */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-pink-400" />
                    <h4 className="text-sm font-semibold">Features</h4>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg glass">
                    <div className="space-y-0.5">
                      <Label className="text-sm">Emotion Intelligence</Label>
                      <p className="text-xs text-muted-foreground">
                        Detect and respond to emotional cues
                      </p>
                    </div>
                    <Switch
                      checked={config.emotionEnabled}
                      onCheckedChange={onToggleEmotion}
                    />
                  </div>
                </div>
              </TabsContent>

              {/* Prompt Tab */}
              <TabsContent value="prompt" className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-xs text-muted-foreground">
                      System Prompt
                    </Label>
                    <Textarea
                      value={config.systemPrompt}
                      onChange={(e) => onUpdateSystemPrompt(e.target.value)}
                      placeholder="Define the agent's personality and behavior..."
                      className="glass min-h-[200px] text-sm"
                    />
                    <p className="text-[10px] text-muted-foreground/50">
                      This prompt defines how the agent behaves and responds.
                    </p>
                  </div>

                  <Separator className="bg-white/5" />

                  <div className="space-y-2">
                    <Label className="text-xs text-muted-foreground">
                      Greeting Message
                    </Label>
                    <Input
                      value={config.greeting}
                      onChange={(e) => onUpdateGreeting(e.target.value)}
                      placeholder="Enter the initial greeting..."
                      className="glass text-sm"
                    />
                    <p className="text-[10px] text-muted-foreground/50">
                      The first message the agent will speak when connected.
                    </p>
                  </div>
                </div>
              </TabsContent>

              {/* Tools Tab */}
              <TabsContent value="tools" className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <Wrench className="w-4 h-4 text-amber-400" />
                  <h4 className="text-sm font-semibold">Available Tools</h4>
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  Enable or disable tools the agent can use during
                  conversations.
                </p>

                <div className="space-y-2">
                  {tools.map((tool) => (
                    <div
                      key={tool.name}
                      className="flex items-center justify-between p-3 rounded-lg glass glass-hover"
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <Label className="text-sm font-medium">
                            {tool.name
                              .split("_")
                              .map(
                                (w) =>
                                  w.charAt(0).toUpperCase() + w.slice(1)
                              )
                              .join(" ")}
                          </Label>
                          {tool.enabled && (
                            <Badge
                              variant="success"
                              className="text-[10px] px-1.5 py-0"
                            >
                              Active
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {tool.description}
                        </p>
                      </div>
                      <Switch
                        checked={tool.enabled}
                        onCheckedChange={() => onToggleTool(tool.name)}
                      />
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>

            {/* Reset button */}
            <Separator className="bg-white/5 my-6" />
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="w-full glass glass-hover gap-2"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset to Defaults
            </Button>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
