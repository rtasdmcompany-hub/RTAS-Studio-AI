import { NextResponse } from "next/server";
import {
  exposesVerificationLinkOnPage,
  getEmailDeliveryMode,
} from "@/lib/env";
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

    const mode = getEmailDeliveryMode();

    return NextResponse.json({
      ok: true,
      email: result.maskedEmail,
      message:
        mode === "smtp" || mode === "resend"
          ? "Confirmation email sent. Check your inbox and spam folder."
          : "Confirmation link ready. Use the button below to confirm your account.",
      realInboxDelivery: mode === "smtp" || mode === "resend",
      devVerificationUrl: exposesVerificationLinkOnPage(mode)
        ? result.verifyUrl
        : undefined,
    });
  } catch {
    return NextResponse.json(
      { error: "Could not resend confirmation email." },
      { status: 500 }
    );
  }
}
