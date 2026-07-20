#!/usr/bin/env node
/**
 * Push production env keys from apps/web/.env.local to Vercel.
 * Requires VERCEL_TOKEN. Never logs secret values.
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = join(__dirname, "..");
const monorepoRoot = join(webRoot, "..", "..");
const envPath = join(webRoot, ".env.local");
const TARGET_ENVS = ["production", "preview", "development"];

const KEYS = [
  "DATABASE_URL",
  "DATABASE_URL_DIRECT",
  "NEXT_PUBLIC_SUPABASE_URL",
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
  "SUPABASE_URL",
  "SUPABASE_ANON_KEY",
  "SUPABASE_SERVICE_ROLE_KEY",
  "NEXTAUTH_URL",
  "NEXTAUTH_SECRET",
  "NEXT_PUBLIC_APP_URL",
  "GOOGLE_CLIENT_ID",
  "GOOGLE_CLIENT_SECRET",
  "NEXT_PUBLIC_GOOGLE_AUTH_ENABLED",
  "GOOGLE_OAUTH_REDIRECT_URI",
  "GOOGLE_OAUTH_JS_ORIGIN",
  "FAL_KEY",
  "FAL_ADMIN_API_KEY",
  "RESEND_API_KEY",
  "EMAIL_FROM",
  "FASTAPI_URL",
  "NEXT_PUBLIC_FASTAPI_URL",
  "NEXT_PUBLIC_PAYMENT_PROVIDER",
  "PADDLE_WEBHOOK_SECRET",
  "PADDLE_API_KEY",
  "RUNPOD_API_KEY",
  "NEXT_PUBLIC_PADDLE_CLIENT_TOKEN",
  "NEXT_PUBLIC_PADDLE_CHECKOUT_URL",
  "NEXT_PUBLIC_PADDLE_TESTER_CHECKOUT_URL",
  "NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL",
  "NEXT_PUBLIC_PADDLE_PREMIUM_CHECKOUT_URL",
  "PADDLE_TESTER_PRICE_ID",
  "PADDLE_STANDARD_PRICE_ID",
  "PADDLE_PREMIUM_PRICE_ID",
  "LEMONSQUEEZY_WEBHOOK_SECRET",
  "LEMONSQUEEZY_STORE_ID",
  "LEMONSQUEEZY_VARIANT_ID",
  "NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL",
  "RTAS_ADMIN_SECRET",
  "RTAS_GENERATION_WEBHOOK_SECRET",
  "AI_BACKEND_SECRET",
  "GITHUB_TOKEN",
  "KV_REST_API_URL",
  "KV_REST_API_TOKEN",
  "UPSTASH_REDIS_REST_URL",
  "UPSTASH_REDIS_REST_TOKEN",
  "REPLICATE_API_TOKEN",
];

function parseEnv(text) {
  const map = new Map();
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    map.set(key, value);
  }
  return map;
}

if (!existsSync(envPath)) {
  console.error("[vercel-env-sync] Missing .env.local");
  process.exit(1);
}

const vars = parseEnv(readFileSync(envPath, "utf8"));
const token = vars.get("VERCEL_TOKEN")?.trim();
if (!token) {
  console.error("[vercel-env-sync] VERCEL_TOKEN missing in .env.local");
  process.exit(1);
}

const npx = process.platform === "win32" ? "npx.cmd" : "npx";
const env = { ...process.env, VERCEL_TOKEN: token };
// Target whichever linked Vercel project matches where the script is run from.
// (web uses `apps/web/.vercel`, api uses `apps/backend/.vercel`)
const cwd = existsSync(join(process.cwd(), ".vercel", "project.json"))
  ? process.cwd()
  : existsSync(join(monorepoRoot, "vercel.json"))
    ? monorepoRoot
    : webRoot;

let ok = 0;
let fail = 0;
let skipped = 0;

for (const key of KEYS) {
  const value = vars.get(key)?.trim();
  // Your local env may contain placeholder markers to avoid exposing secrets in the repo.
  // Never overwrite the real Vercel secret store with placeholder strings.
  if (!value || value === "[SENSITIVE]") {
    skipped += 1;
    console.log(`[vercel-env-sync] skip ${key} (empty)`);
    continue;
  }

  for (const target of TARGET_ENVS) {
    const add = spawnSync(
      npx,
      [
        "-y",
        "vercel@56.3.2",
        "env",
        "add",
        key,
        target,
        "--force",
        "--yes",
        "-t",
        token,
      ],
      {
        cwd,
        env,
        input: `${value}\n`,
        stdio: ["pipe", "pipe", "pipe"],
        encoding: "utf8",
        shell: process.platform === "win32",
      }
    );

    if (add.status === 0) {
      console.log(`[vercel-env-sync] set ${key} (${target})`);
      ok += 1;
    } else {
      const err = (add.stderr || add.stdout || "").trim().slice(0, 200);
      console.error(`[vercel-env-sync] failed ${key} (${target}): ${err}`);
      fail += 1;
    }
  }
}

console.log(
  `[vercel-env-sync] done (${ok} set, ${skipped} skipped, ${fail} failed)`
);
process.exit(fail > 0 ? 1 : 0);
