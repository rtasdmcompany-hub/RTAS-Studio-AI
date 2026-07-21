import { createHmac, timingSafeEqual } from "crypto";
import { PRODUCT_NAME } from "@rtas/shared";
import { getEmailDeliveryMode, getNextAuthSecret, getNextAuthUrl } from "@/lib/env";
import { findAuthUserByEmail, findAuthUserById, updateCredentialsPasswordHash } from "@/lib/server/auth-users";
import { maskEmail } from "@/lib/server/email-verification";
import { sendEmail } from "@/lib/server/mailer";
import type { EmailDeliveryMode } from "@/lib/env";
import bcrypt from "bcryptjs";

const TOKEN_TTL_MS = 60 * 60 * 1000;
const BCRYPT_ROUNDS = 10;
const TOKEN_PREFIX = "reset";

function signResetPayload(
  userId: string,
  email: string,
  expiresAt: number
): string {
  const payload = `${TOKEN_PREFIX}:${userId}:${email}:${expiresAt}`;
  const data = Buffer.from(payload, "utf8").toString("base64url");
  const sig = createHmac("sha256", getNextAuthSecret())
    .update(payload)
    .digest("base64url");
  return `${data}.${sig}`;
}

function parseSignedResetToken(
  token: string
): { userId: string; email: string } | null {
  const dot = token.indexOf(".");
  if (dot <= 0) return null;

  const data = token.slice(0, dot);
  const sig = token.slice(dot + 1);
  if (!data || !sig) return null;

  let payload = "";
  try {
    payload = Buffer.from(data, "base64url").toString("utf8");
  } catch {
    return null;
  }

  const parts = payload.split(":");
  if (parts.length !== 4 || parts[0] !== TOKEN_PREFIX) return null;
  const [, userId, email, expStr] = parts;
  const expiresAt = Number(expStr);
  if (!userId || !email || !Number.isFinite(expiresAt)) return null;
  if (Date.now() > expiresAt) return null;

  const expected = createHmac("sha256", getNextAuthSecret())
    .update(payload)
    .digest("base64url");
  const sigBuf = Buffer.from(sig);
  const expectedBuf = Buffer.from(expected);
  if (
    sigBuf.length !== expectedBuf.length ||
    !timingSafeEqual(sigBuf, expectedBuf)
  ) {
    return null;
  }

  return { userId, email };
}

async function createResetToken(userId: string, email: string): Promise<string> {
  const expiresAtMs = Date.now() + TOKEN_TTL_MS;
  return signResetPayload(userId, email, expiresAtMs);
}

function buildResetEmail(name: string, resetUrl: string) {
  const subject = `Reset your ${PRODUCT_NAME} password`;
  const html = `
    <div style="font-family:Segoe UI,Arial,sans-serif;line-height:1.6;color:#111;">
      <h2 style="margin:0 0 12px;">Reset your password</h2>
      <p>Hi ${name},</p>
      <p>We received a request to reset the password for your ${PRODUCT_NAME} account. Click the button below to choose a new password.</p>
      <p style="margin:28px 0;">
        <a href="${resetUrl}" style="background:#7c5cff;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;display:inline-block;font-weight:600;">
          Reset password
        </a>
      </p>
      <p style="font-size:13px;color:#555;">This link expires in 1 hour. If you did not request a password reset, you can ignore this email.</p>
      <p style="font-size:12px;color:#777;word-break:break-all;">Or copy this link: ${resetUrl}</p>
    </div>
  `.trim();

  const text = [
    `Hi ${name},`,
    "",
    `Reset your ${PRODUCT_NAME} password:`,
    resetUrl,
    "",
    "This link expires in 1 hour.",
  ].join("\n");

  return { subject, html, text };
}

export async function sendPasswordResetEmailForUser(input: {
  userId: string;
  email: string;
  name: string;
}): Promise<
  | {
      ok: true;
      resetUrl: string;
      emailSent: boolean;
      delivery: EmailDeliveryMode;
      devPreviewPath?: string;
      deliveryError?: string;
    }
  | { ok: false; error: string }
> {
  const user = await findAuthUserById(input.userId);
  if (!user) return { ok: false, error: "Account not found." };
  if (!user.passwordHash) {
    return {
      ok: false,
      error: "This account uses Google sign-in. Continue with Google instead.",
    };
  }

  const token = await createResetToken(input.userId, input.email);
  const baseUrl = getNextAuthUrl().replace(/\/$/, "");
  const resetUrl = `${baseUrl}/auth/reset-password?token=${encodeURIComponent(token)}`;
  const { subject, html, text } = buildResetEmail(input.name, resetUrl);

  const sent = await sendEmail({
    to: input.email,
    subject,
    html,
    text,
  });

  if (sent.ok) {
    return {
      ok: true,
      resetUrl,
      emailSent: sent.provider === "resend" || sent.provider === "smtp",
      delivery: sent.provider ?? getEmailDeliveryMode(),
      devPreviewPath: sent.devPreviewPath,
    };
  }

  return {
    ok: true,
    resetUrl,
    emailSent: false,
    delivery: "link-only",
    deliveryError: sent.error ?? "Could not send password reset email.",
  };
}

export async function requestPasswordResetForEmail(
  email: string
): Promise<
  | {
      ok: true;
      maskedEmail?: string;
      resetUrl?: string;
      emailSent: boolean;
      delivery: EmailDeliveryMode;
      deliveryError?: string;
      generic?: boolean;
    }
  | { ok: false; error: string }
> {
  const normalized = email.trim().toLowerCase();
  if (!normalized.includes("@")) {
    return { ok: false, error: "Enter a valid email address." };
  }

  const user = await findAuthUserByEmail(normalized);
  if (!user) {
    return {
      ok: true,
      emailSent: false,
      delivery: getEmailDeliveryMode(),
      generic: true,
    };
  }

  if (!user.passwordHash) {
    return {
      ok: false,
      error: "This account uses Google sign-in. Continue with Google instead.",
    };
  }

  const sent = await sendPasswordResetEmailForUser({
    userId: user.id,
    email: user.email,
    name: user.name,
  });

  if (!sent.ok) return sent;

  return {
    ok: true,
    maskedEmail: maskEmail(user.email),
    resetUrl: sent.resetUrl,
    emailSent: sent.emailSent,
    delivery: sent.delivery,
    deliveryError: sent.deliveryError,
  };
}

export async function resetPasswordWithToken(
  token: string,
  newPassword: string
): Promise<{ ok: true; email: string } | { ok: false; error: string }> {
  const trimmed = token.trim();
  if (!trimmed) {
    return { ok: false, error: "Invalid or missing reset link." };
  }
  if (newPassword.length < 8) {
    return { ok: false, error: "Password must be at least 8 characters." };
  }

  const signed = parseSignedResetToken(trimmed);
  if (!signed) {
    return {
      ok: false,
      error: "This password reset link is invalid or has expired.",
    };
  }

  const user = await findAuthUserById(signed.userId);
  if (!user) {
    return { ok: false, error: "Account not found." };
  }
  if (!user.passwordHash) {
    return {
      ok: false,
      error: "This account uses Google sign-in. Continue with Google instead.",
    };
  }
  if (user.email.toLowerCase() !== signed.email.toLowerCase()) {
    return { ok: false, error: "Invalid reset link." };
  }

  const passwordHash = await bcrypt.hash(newPassword, BCRYPT_ROUNDS);
  const updated = await updateCredentialsPasswordHash(user.id, passwordHash);
  if (!updated) {
    return { ok: false, error: "Could not update password. Try again." };
  }

  return { ok: true, email: user.email };
}
