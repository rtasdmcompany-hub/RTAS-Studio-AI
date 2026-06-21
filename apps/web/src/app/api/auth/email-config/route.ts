import { NextResponse } from "next/server";
import {
  canDeliverEmailToAnyInbox,
  getEmailDeliveryMode,
  getResendApiKey,
  getSmtpConfig,
  isEmailDeliveryConfigured,
  isResendSandboxFrom,
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
  const realInboxDelivery = canDeliverEmailToAnyInbox();

  return NextResponse.json({
    configured:
      isEmailDeliveryConfigured() ||
      mode === "dev-file" ||
      mode === "link-only",
    mode,
    realInboxDelivery,
    linkOnlyConfirmation: !realInboxDelivery,
    resendSandboxFrom: isResendSandboxFrom(),
    smtpNeedsAppPassword:
      process.env.NODE_ENV === "development" && Boolean(smtpUser && !smtpPass),
    resendNeedsApiKey: !getResendApiKey() && !getSmtpConfig(),
  });
}