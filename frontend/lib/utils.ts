import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

export function generateRoomName(): string {
  return `voice_room_${Math.floor(Math.random() * 10_000)}`;
}

export function generateParticipantIdentity(): string {
  return `user_${Math.floor(Math.random() * 10_000)}`;
}
