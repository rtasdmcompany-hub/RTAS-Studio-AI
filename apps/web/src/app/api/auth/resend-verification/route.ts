import { NextResponse } from "next/server";
import { resendVerificationForEmail } from "@/lib/server/email-verification";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `resend-verification:${ip}`,
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
      `resend-verification-email:${email.toLowerCase()}`,
      3,
      60 * 60_000
    );
    if (!emailLimited.ok) return rateLimitResponse(emailLimited.retryAfterSec);

    const result = await resendVerificationForEmail(email);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    return NextResponse.json({
      ok: true,
      email: result.maskedEmail,
      message: result.emailSent
        ? "Confirmation email sent. Check your inbox and spam folder."
        : "Confirmation link ready. Use the button below to confirm your account.",
      emailSent: result.emailSent,
      realInboxDelivery: result.emailSent,
      devVerificationUrl: result.emailSent ? undefined : result.verifyUrl,
      deliveryError: result.deliveryError,
    });
  } catch {
    return NextResponse.json(
      { error: "Could not resend confirmation email." },
      { status: 500 }
    );
  }
}
