import { NextResponse } from "next/server";
import {
  getGoogleClientId,
  getGoogleOAuthConsoleSettings,
  getNextAuthUrl,
  isGoogleAuthConfigured,
} from "@/lib/env";

/** Public Google OAuth console checklist — no secrets. */
export async function GET() {
  const oauth = getGoogleOAuthConsoleSettings();
  return NextResponse.json({
    configured: isGoogleAuthConfigured(),
    nextAuthUrl: getNextAuthUrl(),
    clientIdSuffix: getGoogleClientId().slice(-24) || null,
    authorizedRedirectUris: oauth.redirectUris,
    authorizedJavaScriptOrigins: oauth.javascriptOrigins,
    configFile: "apps/web/google-oauth.config.json",
  });
}
