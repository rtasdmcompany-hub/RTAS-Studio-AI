import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";
import { isPrismaConfigured, prisma } from "@/lib/prisma";

export const runtime = "nodejs";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`newsletter:${ip}`, 8, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: { email?: string; name?: string } = {};
  try {
    body = (await request.json()) as { email?: string; name?: string };
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const email = (body.email ?? "").trim().toLowerCase();
  const name = (body.name ?? "").trim().slice(0, 120);
  if (!EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "Valid email required." }, { status: 400 });
  }

  if (!isPrismaConfigured()) {
    return NextResponse.json(
      {
        error:
          "Newsletter storage is not configured on this environment. Email contact@rtasstudio.com to join the list.",
        code: "DB_UNAVAILABLE",
      },
      { status: 503 }
    );
  }

  try {
    await prisma.newsletterSubscriber.upsert({
      where: { email },
      create: {
        id: randomUUID(),
        email,
        name,
        status: "subscribed",
        source: "web",
      },
      update: {
        name: name || undefined,
        status: "subscribed",
        unsubscribedAt: null,
      },
    });
    return NextResponse.json({
      ok: true,
      message: "Subscribed. You can manage preferences after signing in.",
    });
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error
            ? err.message
            : "Could not save subscription. Migration may be pending.",
      },
      { status: 500 }
    );
  }
}
