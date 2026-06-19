import { NextResponse } from "next/server";
import {
  getGoogleClientId,
  getGoogleOAuthCallbackUrl,
  getNextAuthUrl,
  isGoogleAuthConfigured,
} from "@/lib/env";
import { findAuthUserByEmail, isEmailVerified } from "@/lib/server/auth-users";

/** Login troubleshooting — no secrets returned. */
export async function GET(request: Request) {
  const email = new URL(request.url).searchParams.get("email")?.trim() ?? "";

  const google = {
    configured: isGoogleAuthConfigured(),
    clientIdSuffix: getGoogleClientId().slice(-24) || null,
    callbackUrl: getGoogleOAuthCallbackUrl(),
    nextAuthUrl: getNextAuthUrl(),
  };

  let account: {
    exists: boolean;
    emailVerified?: boolean;
    hasPassword?: boolean;
    hasGoogle?: boolean;
  } = { exists: false };

  if (email) {
    const user = await findAuthUserByEmail(email);
    if (user) {
      account = {
        exists: true,
        emailVerified: isEmailVerified(user),
        hasPassword: Boolean(user.passwordHash),
        hasGoogle: user.provider === "google" || Boolean(user.image),
      };
    }
  }

  return NextResponse.json({ google, account });
}
