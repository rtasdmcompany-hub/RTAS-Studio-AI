import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";
import { findAuthUserByEmail, isEmailVerified } from "@/lib/server/auth-users";

/**
 * Non-oracle verification hint for the login UX.
 * Never accepts a password — only reports whether an email is pending verification
 * when the account exists. Always returns a uniform shape to reduce enumeration.
 */
export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `check-verification:${ip}`,
    20,
    60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  try {
    const body = (await request.json()) as { email?: string };
    const email = body.email?.trim().toLowerCase() ?? "";

    // Uniform response when input is incomplete.
    if (!email || !email.includes("@")) {
      return NextResponse.json({ unverified: false });
    }

    const record = await findAuthUserByEmail(email);
    if (!record) {
      return NextResponse.json({ unverified: false });
    }

    return NextResponse.json({
      unverified: !isEmailVerified(record),
    });
  } catch {
    return NextResponse.json({ unverified: false });
  }
}
