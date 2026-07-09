import { NextResponse } from "next/server";
import {
  getGoogleClientId,
  getGoogleOAuthCallbackUrl,
  getNextAuthUrl,
  isGoogleAuthConfigured,
} from "@/lib/env";
import { findAuthUserByEmail, isEmailVerified } from "@/lib/server/auth-users";
import {
  checkRateLimit,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";

/**
 * Login troubleshooting — no secrets returned.
 * Account details are only returned for the queried email after rate limiting
 * to reduce account enumeration abuse.
 */
export async function GET(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = checkRateLimit(`login-help:${ip}`, 20, 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  const email = new URL(request.url).searchParams.get("email")?.trim() ?? "";

  const google = {
    configured: isGoogleAuthConfigured(),
    clientIdSuffix: getGoogleClientId().slice(-24) || null,
    callbackUrl: getGoogleOAuthCallbackUrl(),
    nextAuthUrl: getNextAuthUrl(),
  };

  // Always return a stable shape; never expose hasPassword/hasGoogle to anonymous callers.
  let account: { exists: boolean; emailVerified?: boolean } = { exists: false };

  if (email) {
    const user = await findAuthUserByEmail(email);
    if (user) {
      account = {
        exists: true,
        emailVerified: isEmailVerified(user),
      };
    }
  }

  return NextResponse.json({ google, account });
}
