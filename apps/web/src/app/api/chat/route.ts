import { NextResponse } from "next/server";
import { getChatReply, type ChatMessage } from "@/lib/live-chat";

export async function POST(request: Request) {
  let body: { message?: string; history?: ChatMessage[] } = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  const message = typeof body.message === "string" ? body.message.trim() : "";
  if (!message || message.length > 2000) {
    return NextResponse.json(
      { error: "Message is required (max 2000 characters)." },
      { status: 400 }
    );
  }

  const history = Array.isArray(body.history)
    ? body.history
        .filter(
          (m): m is ChatMessage =>
            m &&
            typeof m === "object" &&
            (m.role === "user" || m.role === "assistant") &&
            typeof m.content === "string"
        )
        .slice(-12)
    : [];

  const reply = getChatReply(message, history);

  return NextResponse.json({ reply });
}
