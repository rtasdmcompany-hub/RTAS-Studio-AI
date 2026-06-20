import { randomBytes } from "crypto";
import { promises as fs } from "fs";
import path from "path";
import { PRODUCT_NAME } from "@rtas/shared";
import { getNextAuthUrl } from "@/lib/env";
import {
  findAuthUserByEmail,
  findAuthUserById,
  isEmailVerified,
  markAuthUserEmailVerified,
} from "@/lib/server/auth-users";
import { sendEmail } from "@/lib/server/mailer";
import type { EmailDeliveryMode } from "@/lib/env";

import { getServerDataDir } from "@/lib/server/data-dir";

const DATA_DIR = getServerDataDir();
const TOKENS_FILE = path.join(DATA_DIR, "email-verification-tokens.json");
const TOKEN_TTL_MS = 24 * 60 * 60 * 1000;

type VerificationTokenRecord = {
  userId: string;
  email: string;
  expiresAt: string;
  createdAt: string;
};

type VerificationTokenMap = Record<string, VerificationTokenRecord>;

async function readTokens(): Promise<VerificationTokenMap> {
  try {
    const raw = await fs.readFile(TOKENS_FILE, "utf-8");
    return JSON.parse(raw) as VerificationTokenMap;
  } catch {
    return {};
  }
}

async function writeTokens(map: VerificationTokenMap) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.writeFile(TOKENS_FILE, JSON.stringify(map, null, 2), "utf-8");
}

function purgeExpired(map: VerificationTokenMap): VerificationTokenMap {
  const now = Date.now();
  const next: VerificationTokenMap = {};
  for (const [token, record] of Object.entries(map)) {
    if (new Date(record.expiresAt).getTime() > now) {
      next[token] = record;
    }
  }
  return next;
}

export function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!local || !domain) return email;
  const visible = local.length <= 2 ? local[0] ?? "*" : `${local.slice(0, 2)}***`;
  return `${visible}@${domain}`;
}

async function createVerificationToken(userId: string, email: string): Promise<string> {
  const token = randomBytes(32).toString("hex");
  const now = new Date();
  const expiresAt = new Date(now.getTime() + TOKEN_TTL_MS);

  let map = purgeExpired(await readTokens());
  map = Object.fromEntries(
    Object.entries(map).filter(([, record]) => record.userId !== userId)
  );

  map[token] = {
    userId,
    email,
    expiresAt: expiresAt.toISOString(),
    createdAt: now.toISOString(),
  };

  await writeTokens(map);
  return token;
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
      delivery: EmailDeliveryMode;
      devPreviewPath?: string;
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

  if (!sent.ok) {
    return { ok: false, error: sent.error ?? "Could not send confirmation email." };
  }

  return {
    ok: true,
    verifyUrl,
    delivery: sent.provider ?? "dev-file",
    devPreviewPath: sent.devPreviewPath,
  };
}

export async function verifyEmailWithToken(
  token: string
): Promise<{ ok: true; email: string } | { ok: false; error: string }> {
  const trimmed = token.trim();
  if (!trimmed) return { ok: false, error: "Invalid confirmation link." };

  const map = purgeExpired(await readTokens());
  const record = map[trimmed];
  if (!record) {
    return { ok: false, error: "This confirmation link is invalid or has expired." };
  }

  if (new Date(record.expiresAt).getTime() <= Date.now()) {
    delete map[trimmed];
    await writeTokens(map);
    return { ok: false, error: "This confirmation link has expired. Request a new one." };
  }

  const user = await findAuthUserById(record.userId);
  if (!user) {
    return { ok: false, error: "Account not found." };
  }

  await markAuthUserEmailVerified(user.id);

  delete map[trimmed];
  await writeTokens(map);

  return { ok: true, email: user.email };
}

export async function resendVerificationForEmail(
  email: string
): Promise<
  | {
      ok: true;
      maskedEmail: string;
      verifyUrl: string;
      delivery: EmailDeliveryMode;
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
    delivery: sent.delivery,
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
