import { NextResponse } from "next/server";
import { type GenerateBody } from "@/lib/generation";
import {
  requireApiSession,
  checkRateLimitAsync,
  rateLimitResponse,
  clientIpFromRequest,
} from "@/lib/server/api-auth";
import { orchestrateGeneration } from "@/lib/server/generation-orchestrator";

export const runtime = "nodejs";
export const maxDuration = 300;

const AUTH_REQUIRED_BODY = {
  error: "Authentication required. Please log in to access the studio.",
} as const;

/**
 * Credit-guarded generation gateway.
 * Delegates to the central AI orchestrator — no provider logic in this route.
 */
export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) {
    return NextResponse.json(AUTH_REQUIRED_BODY, { status: auth.response.status });
  }

  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `generate:${auth.userId}:${ip}`,
    30,
    60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  const body = (await request.json()) as GenerateBody & {
    jobId?: string;
    profile?: { subscriptionActive?: boolean; credits?: number };
    previewOnly?: boolean;
    useFreeTrial?: boolean;
    deviceFingerprint?: string;
  };

  return orchestrateGeneration({
    userId: auth.userId,
    request,
    body,
  });
}
