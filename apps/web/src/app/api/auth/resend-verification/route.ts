import { NextResponse } from "next/server";
import { resendVerificationForEmail } from "@/lib/server/email-verification";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { email?: string };
    const email = body.email?.trim() ?? "";
    if (!email) {
      return NextResponse.json({ error: "Email is required." }, { status: 400 });
    }

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
