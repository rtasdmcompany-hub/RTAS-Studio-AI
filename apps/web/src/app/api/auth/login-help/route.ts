import { NextResponse } from "next/server";
import {
  getGoogleClientId,
  getGoogleOAuthCallbackUrl,
  getNextAuthUrl,
  isGoogleAuthConfigured,
} from "@/lib/env";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";

/**
 * Login troubleshooting — no secrets, no account enumeration.
 * Always returns a stable public shape (Google OAuth config hints only).
 */
export async function GET(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`login-help:${ip}`, 10, 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  // Intentionally ignore ?email= — never confirm account existence.
  void new URL(request.url).searchParams.get("email");

  const google = {
    configured: isGoogleAuthConfigured(),
    clientIdSuffix: getGoogleClientId().slice(-24) || null,
    callbackUrl: getGoogleOAuthCallbackUrl(),
    nextAuthUrl: getNextAuthUrl(),
  };

  return NextResponse.json({
    google,
    account: { exists: false },
  });
}
