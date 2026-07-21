import { NextResponse } from "next/server";
import { requestPasswordResetForEmail } from "@/lib/server/password-reset";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `forgot-password:${ip}`,
    10,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  try {
    const body = (await request.json()) as { email?: string };
    const email = body.email?.trim() ?? "";
    if (!email) {
      return NextResponse.json({ error: "Email is required." }, { status: 400 });
    }

    const emailLimited = await checkRateLimitAsync(
      `forgot-password-email:${email.toLowerCase()}`,
      3,
      60 * 60_000
    );
    if (!emailLimited.ok) return rateLimitResponse(emailLimited.retryAfterSec);

    const result = await requestPasswordResetForEmail(email);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    if (result.generic) {
      return NextResponse.json({
        ok: true,
        message:
          "If an account with this email exists, we sent a password reset link. Check your inbox and spam folder.",
        emailSent: false,
      });
    }

    return NextResponse.json({
      ok: true,
      email: result.maskedEmail,
      message: result.emailSent
        ? "Password reset email sent. Check your inbox and spam folder."
        : "Password reset link ready. Use the button below to choose a new password.",
      emailSent: result.emailSent,
      realInboxDelivery: result.emailSent,
      devResetUrl: result.emailSent ? undefined : result.resetUrl,
      deliveryError: result.deliveryError,
    });
  } catch {
    return NextResponse.json(
      { error: "Could not send password reset email." },
      { status: 500 }
    );
  }
}
