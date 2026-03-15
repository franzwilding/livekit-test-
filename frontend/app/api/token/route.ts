import { NextResponse } from "next/server";
import { AccessToken, type VideoGrant } from "livekit-server-sdk";

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

export async function POST(req: Request) {
  if (!LIVEKIT_URL || !API_KEY || !API_SECRET) {
    return new NextResponse(
      JSON.stringify({
        error:
          "Server misconfigured. Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET environment variables.",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  let configMetadata = "{}";
  try {
    const body = await req.json();
    if (body.config) {
      configMetadata = JSON.stringify(body.config);
    }
  } catch {
    // No body or invalid JSON is fine - use defaults
  }

  const participantIdentity = `user_${Math.floor(Math.random() * 10_000)}`;
  const roomName = `voice_room_${Math.floor(Math.random() * 10_000)}`;

  const at = new AccessToken(API_KEY, API_SECRET, {
    identity: participantIdentity,
    name: "User",
    ttl: "15m",
    metadata: configMetadata,
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  const token = await at.toJwt();

  return NextResponse.json(
    {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName: "User",
      participantToken: token,
    },
    {
      headers: { "Cache-Control": "no-store" },
    }
  );
}
