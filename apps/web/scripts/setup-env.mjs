#!/usr/bin/env node
/**
 * Bootstrap apps/web/.env.local and apps/backend/.env.
 * Creates missing files; rotates weak NEXTAUTH_SECRET values.
 */
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = join(__dirname, "..");
const backendRoot = join(webRoot, "..", "backend");
const webEnv = join(webRoot, ".env.local");
const backendEnv = join(backendRoot, ".env");

const WEAK_SECRETS = new Set([
  "",
  "generate-with-openssl-rand-base64-32",
  "your-random-secret-here",
  "PLACEHOLDER_RUN_npm_run_setup_env",
  "change-me",
]);

function newSecret() {
  return randomBytes(32).toString("base64");
}

function writeIfMissing(filePath, content, label) {
  if (existsSync(filePath)) {
    console.log(`[skip] ${label} already exists: ${filePath}`);
    return false;
  }
  mkdirSync(dirname(filePath), { recursive: true });
  writeFileSync(filePath, content, "utf8");
  console.log(`[ok] Created ${label}: ${filePath}`);
  return true;
}

function ensureNextAuthSecret(filePath) {
  if (!existsSync(filePath)) return;
  let content = readFileSync(filePath, "utf8");
  const match = content.match(/^NEXTAUTH_SECRET=(.*)$/m);
  const current = (match?.[1] ?? "").trim();
  if (!WEAK_SECRETS.has(current) && current.length >= 32) return;

  const secret = newSecret();
  if (match) {
    content = content.replace(/^NEXTAUTH_SECRET=.*$/m, `NEXTAUTH_SECRET=${secret}`);
  } else {
    content = `NEXTAUTH_SECRET=${secret}\n${content}`;
  }
  writeFileSync(filePath, content, "utf8");
  console.log(`[ok] Set cryptographically strong NEXTAUTH_SECRET in ${filePath}`);
}

const timestamp = new Date().toISOString();
const secret = newSecret();

const webContent = `# =============================================================================
# RTAS Studio AI — local environment (auto-generated ${timestamp})
# Do not commit this file. Regenerate: npm run setup:env
# =============================================================================

# --- NextAuth (required for /studio) ---
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=${secret}

# --- Google OAuth (leave empty for email-only auth / simulation) ---
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
# UI flag; Google button only appears when credentials above are non-empty
NEXT_PUBLIC_GOOGLE_AUTH_ENABLED=true

# --- Cloud AI (optional — empty = demo / simulation playback) ---
# Replicate is consumed by the FastAPI backend; set the same token in apps/backend/.env
REPLICATE_API_TOKEN=

# --- FastAPI backend ---
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# --- Payments (optional) ---
NEXT_PUBLIC_PAYMENT_PROVIDER=paddle
PADDLE_WEBHOOK_SECRET=
NEXT_PUBLIC_PADDLE_CLIENT_TOKEN=
NEXT_PUBLIC_PADDLE_CHECKOUT_URL=
LEMONSQUEEZY_WEBHOOK_SECRET=
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_VARIANT_ID=
NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL=

# --- Legacy Next.js demo keys (optional) ---
RUNWAY_API_KEY=
KLING_API_KEY=
FAL_KEY=
`;

const backendContent = `# =============================================================================
# RTAS Studio AI — FastAPI backend (auto-generated ${timestamp})
# =============================================================================

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001
PUBLIC_BASE_URL=http://localhost:8000

# auto | simulation | replicate | comfyui | diffusers
AI_PROVIDER_MODE=auto

# Leave empty for local simulation / placeholder video delivery
REPLICATE_API_TOKEN=

REPLICATE_CACHE_OUTPUTS_LOCALLY=true
LOCAL_UPLOAD_DIR=data/uploads
LOCAL_OUTPUT_DIR=data/outputs
`;

writeIfMissing(webEnv, webContent, "frontend .env.local");
writeIfMissing(backendEnv, backendContent, "backend .env");
ensureNextAuthSecret(webEnv);

console.log("\nDone. Start stack:");
console.log("  npm run dev          # Next.js");
console.log("  npm run dev:api      # FastAPI\n");
