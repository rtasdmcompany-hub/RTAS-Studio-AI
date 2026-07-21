import { NextResponse } from "next/server";
import { resetPasswordWithToken } from "@/lib/server/password-reset";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `reset-password:${ip}`,
    15,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  try {
    const body = (await request.json()) as {
      token?: string;
      password?: string;
    };
    const token = body.token?.trim() ?? "";
    const password = body.password ?? "";

    if (!token) {
      return NextResponse.json(
        { error: "Invalid or missing reset link." },
        { status: 400 }
      );
    }
    if (!password) {
      return NextResponse.json(
        { error: "Password is required." },
        { status: 400 }
      );
    }

    const result = await resetPasswordWithToken(token, password);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    return NextResponse.json({
      ok: true,
      email: result.email,
      message: "Password updated. Sign in with your new password.",
    });
  } catch {
    return NextResponse.json(
      { error: "Could not reset password." },
      { status: 500 }
    );
  }
}
