import { createHmac, timingSafeEqual } from "crypto";
import { PRODUCT_NAME } from "@rtas/shared";
import { getEmailDeliveryMode, getNextAuthSecret, getNextAuthUrl } from "@/lib/env";
import {
  findAuthUserByEmail,
  findAuthUserById,
  isEmailVerified,
  markAuthUserEmailVerified,
} from "@/lib/server/auth-users";
import { sendEmail } from "@/lib/server/mailer";
import type { EmailDeliveryMode } from "@/lib/env";

const TOKEN_TTL_MS = 24 * 60 * 60 * 1000;

export function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!local || !domain) return email;
  const visible = local.length <= 2 ? local[0] ?? "*" : `${local.slice(0, 2)}***`;
  return `${visible}@${domain}`;
}

function signVerificationPayload(
  userId: string,
  email: string,
  expiresAt: number
): string {
  const payload = `${userId}:${email}:${expiresAt}`;
  const data = Buffer.from(payload, "utf8").toString("base64url");
  const sig = createHmac("sha256", getNextAuthSecret())
    .update(payload)
    .digest("base64url");
  return `${data}.${sig}`;
}

function parseSignedVerificationToken(
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
  if (parts.length !== 3) return null;
  const [userId, email, expStr] = parts;
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

/** Stateless HMAC-signed token — no server-side token files required. */
async function createVerificationToken(userId: string, email: string): Promise<string> {
  const expiresAtMs = Date.now() + TOKEN_TTL_MS;
  return signVerificationPayload(userId, email, expiresAtMs);
}

function buildVerificationEmail(name: string, verifyUrl: string) {
  const subject = `Confirm your ${PRODUCT_NAME} account`;
  const html = `
    <div style="font-family:Segoe UI,Arial,sans-serif;line-height:1.6;color:#111;">
      <h2 style="margin:0 0 12px;">Confirm your email</h2>
      <p>Hi ${name},</p>
      <p>Thanks for signing up for ${PRODUCT_NAME}. Click the button below to confirm your email address and activate your account.</p>
      <p style="margin:28px 0;">
        <a href="${verifyUrl}" style="background:#7c5cff;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;display:inline-block;font-weight:600;">
          Confirm my account
        </a>
      </p>
      <p style="font-size:13px;color:#555;">This link expires in 24 hours. If you did not create an account, you can ignore this email.</p>
      <p style="font-size:12px;color:#777;word-break:break-all;">Or copy this link: ${verifyUrl}</p>
    </div>
  `.trim();

  const text = [
    `Hi ${name},`,
    "",
    `Confirm your ${PRODUCT_NAME} account:`,
    verifyUrl,
    "",
    "This link expires in 24 hours.",
  ].join("\n");

  return { subject, html, text };
}

export async function sendVerificationEmailForUser(input: {
  userId: string;
  email: string;
  name: string;
}): Promise<
  | {
      ok: true;
      verifyUrl: string;
      emailSent: boolean;
      delivery: EmailDeliveryMode;
      devPreviewPath?: string;
      deliveryError?: string;
    }
  | { ok: false; error: string }
> {
  const user = await findAuthUserById(input.userId);
  if (!user) return { ok: false, error: "Account not found." };
  if (isEmailVerified(user)) {
    return { ok: false, error: "Email is already confirmed." };
  }

  const token = await createVerificationToken(input.userId, input.email);
  const baseUrl = getNextAuthUrl().replace(/\/$/, "");
  const verifyUrl = `${baseUrl}/api/auth/verify-email?token=${token}`;
  const { subject, html, text } = buildVerificationEmail(input.name, verifyUrl);

  const sent = await sendEmail({
    to: input.email,
    subject,
    html,
    text,
  });

  if (sent.ok) {
    return {
      ok: true,
      verifyUrl,
      emailSent: sent.provider === "resend" || sent.provider === "smtp",
      delivery: sent.provider ?? getEmailDeliveryMode(),
      devPreviewPath: sent.devPreviewPath,
    };
  }

  // Inbox delivery failed — still return a signed link so the user can confirm on-page.
  return {
    ok: true,
    verifyUrl,
    emailSent: false,
    delivery: "link-only",
    deliveryError: sent.error ?? "Could not send confirmation email.",
  };
}

export async function verifyEmailWithToken(
  token: string
): Promise<{ ok: true; email: string } | { ok: false; error: string }> {
  const trimmed = token.trim();
  if (!trimmed) return { ok: false, error: "Invalid confirmation link." };

  const signed = parseSignedVerificationToken(trimmed);
  if (!signed) {
    return { ok: false, error: "This confirmation link is invalid or has expired." };
  }

  const user = await findAuthUserById(signed.userId);
  if (!user) {
    return { ok: false, error: "Account not found. Sign up again or use Google sign-in." };
  }

  await markAuthUserEmailVerified(user.id);
  return { ok: true, email: user.email };
}

export async function resendVerificationForEmail(
  email: string
): Promise<
  | {
      ok: true;
      maskedEmail: string;
      verifyUrl: string;
      emailSent: boolean;
      delivery: EmailDeliveryMode;
      deliveryError?: string;
    }
  | { ok: false; error: string }
> {
  const user = await findAuthUserByEmail(email);
  if (!user) {
    return {
      ok: false,
      error: "No account found with this email. Sign up first or check the address.",
    };
  }
  if (isEmailVerified(user)) {
    return { ok: false, error: "This email is already confirmed. You can sign in." };
  }
  if (!user.passwordHash) {
    return {
      ok: false,
      error: "This account uses Google sign-in. Continue with Google instead.",
    };
  }

  const sent = await sendVerificationEmailForUser({
    userId: user.id,
    email: user.email,
    name: user.name,
  });

  if (!sent.ok) return sent;

  return {
    ok: true,
    maskedEmail: maskEmail(user.email),
    verifyUrl: sent.verifyUrl,
    emailSent: sent.emailSent,
    delivery: sent.delivery,
    deliveryError: sent.deliveryError,
  };
}

export async function isUnverifiedCredentialsLogin(
  email: string,
  password: string
): Promise<boolean> {
  const user = await findAuthUserByEmail(email);
  if (!user?.passwordHash || isEmailVerified(user)) return false;

  const bcrypt = await import("bcryptjs");
  return bcrypt.compare(password, user.passwordHash);
}
