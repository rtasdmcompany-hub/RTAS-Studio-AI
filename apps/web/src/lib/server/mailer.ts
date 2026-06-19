import { promises as fs } from "fs";
import path from "path";
import {
  getEmailFrom,
  getResendApiKey,
  getSmtpConfig,
  isEmailDeliveryConfigured,
} from "@/lib/env";

export type SendEmailInput = {
  to: string;
  subject: string;
  html: string;
  text: string;
};

export type SendEmailResult = {
  ok: boolean;
  provider?: "resend" | "smtp" | "dev-file";
  devPreviewPath?: string;
  error?: string;
};

const DEV_EMAIL_DIR = path.join(process.cwd(), ".data", "dev-emails");

async function sendViaResend(input: SendEmailInput): Promise<SendEmailResult> {
  const apiKey = getResendApiKey();
  const from = getEmailFrom();

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [input.to],
      subject: input.subject,
      html: input.html,
      text: input.text,
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    return { ok: false, error: `Resend error (${res.status}): ${body}` };
  }

  return { ok: true, provider: "resend" };
}

async function sendViaSmtp(input: SendEmailInput): Promise<SendEmailResult> {
  const smtp = getSmtpConfig();
  if (!smtp) return { ok: false, error: "SMTP is not configured." };

  const nodemailer = await import("nodemailer");
  const transport = nodemailer.createTransport({
    host: smtp.host,
    port: smtp.port,
    secure: smtp.secure,
    auth: {
      user: smtp.user,
      pass: smtp.pass,
    },
  });

  await transport.sendMail({
    from: getEmailFrom(),
    to: input.to,
    subject: input.subject,
    html: input.html,
    text: input.text,
  });

  return { ok: true, provider: "smtp" };
}

async function sendViaDevFile(input: SendEmailInput): Promise<SendEmailResult> {
  await fs.mkdir(DEV_EMAIL_DIR, { recursive: true });
  const safeTo = input.to.replace(/[^a-zA-Z0-9@._-]/g, "_");
  const filename = `${Date.now()}-${safeTo}.html`;
  const filePath = path.join(DEV_EMAIL_DIR, filename);
  const content = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>${input.subject}</title></head>
<body>
<p><strong>To:</strong> ${input.to}</p>
<p><strong>Subject:</strong> ${input.subject}</p>
<hr />
${input.html}
</body>
</html>`;
  await fs.writeFile(filePath, content, "utf-8");
  console.info(`[mailer:dev] Saved verification email to ${filePath}`);
  return { ok: true, provider: "dev-file", devPreviewPath: filePath };
}

export async function sendEmail(input: SendEmailInput): Promise<SendEmailResult> {
  if (getResendApiKey()) {
    const result = await sendViaResend(input);
    if (result.ok) return result;
    console.error("[mailer] Resend failed:", result.error);
  }

  const smtp = getSmtpConfig();
  if (smtp) {
    try {
      return await sendViaSmtp(input);
    } catch (err) {
      const message = err instanceof Error ? err.message : "SMTP send failed.";
      console.error("[mailer] SMTP failed:", message);
      if (process.env.NODE_ENV === "development") {
        return sendViaDevFile(input);
      }
      return { ok: false, error: message };
    }
  }

  if (process.env.NODE_ENV === "development") {
    return sendViaDevFile(input);
  }

  return {
    ok: false,
    error: isEmailDeliveryConfigured()
      ? "Email delivery failed."
      : "Email is not configured. Set RESEND_API_KEY or SMTP_* in apps/web/.env.local.",
  };
}
