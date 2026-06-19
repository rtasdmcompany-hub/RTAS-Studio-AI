import { NextResponse } from "next/server";
import { getNextAuthUrl } from "@/lib/env";
import { verifyEmailWithToken } from "@/lib/server/email-verification";

export async function GET(request: Request) {
  const token = new URL(request.url).searchParams.get("token");
  const base = getNextAuthUrl().replace(/\/$/, "");

  if (!token) {
    return NextResponse.redirect(
      `${base}/auth/login?error=invalid_verification_link`
    );
  }

  const result = await verifyEmailWithToken(token);
  if (!result.ok) {
    return NextResponse.redirect(
      `${base}/auth/login?error=${encodeURIComponent(result.error)}`
    );
  }

  return NextResponse.redirect(
    `${base}/auth/login?verified=1&email=${encodeURIComponent(result.email)}`
  );
}
