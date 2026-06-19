import { NextResponse } from "next/server";
import {
  getEmailDeliveryMode,
  getResendApiKey,
  getSmtpConfig,
  isEmailDeliveryConfigured,
} from "@/lib/env";

function readSmtpUser(): string {
  return process.env.SMTP_USER?.trim() ?? "";
}

function readSmtpPass(): string {
  return process.env.SMTP_PASS?.trim() ?? "";
}

export async function GET() {
  const mode = getEmailDeliveryMode();
  const smtpUser = readSmtpUser();
  const smtpPass = readSmtpPass();
  const realInboxDelivery = mode === "resend" || mode === "smtp";

  return NextResponse.json({
    configured: isEmailDeliveryConfigured() || mode === "dev-file",
    mode,
    realInboxDelivery,
    smtpNeedsAppPassword: Boolean(smtpUser && !smtpPass),
    resendNeedsApiKey: !getResendApiKey() && !getSmtpConfig(),
  });
}