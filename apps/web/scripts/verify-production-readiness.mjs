#!/usr/bin/env node
/**
 * Production readiness checklist for commercial launch.
 * Reads apps/web/.env.local (or process.env) and reports go/no-go for ops secrets.
 *
 * Exit 0 = all required production keys present (or RTAS_ALLOW_INCOMPLETE_ENV=1).
 * Exit 1 = missing critical production configuration.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const envPath = join(webRoot, ".env.local");

function parseEnvFile(raw) {
  const vars = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    vars[trimmed.slice(0, eq).trim()] = val;
  }
  return vars;
}

const fileVars = existsSync(envPath)
  ? parseEnvFile(readFileSync(envPath, "utf8"))
  : {};
const env = { ...fileVars, ...process.env };

function has(key) {
  const v = (env[key] ?? "").trim();
  return v.length > 0 && !["change-me", "generate-with-openssl-rand-base64-32"].includes(v);
}

const provider = (env.NEXT_PUBLIC_PAYMENT_PROVIDER || "paddle").toLowerCase();

const checks = [
  { key: "NEXTAUTH_SECRET", required: true, group: "secrets" },
  { key: "NEXTAUTH_URL", required: true, group: "secrets" },
  { key: "NEXT_PUBLIC_APP_URL", required: true, group: "secrets" },
  { key: "DATABASE_URL", required: true, group: "secrets" },
  { key: "FASTAPI_URL", required: true, group: "gpu" },
  {
    key: "KV_REST_API_URL",
    required: false,
    alt: ["UPSTASH_REDIS_REST_URL"],
    group: "secrets",
    label: "KV / Redis URL",
  },
  {
    key: "KV_REST_API_TOKEN",
    required: false,
    alt: ["UPSTASH_REDIS_REST_TOKEN"],
    group: "secrets",
    label: "KV / Redis token",
  },
  {
    key: "FAL_KEY",
    required: false,
    alt: ["REPLICATE_API_TOKEN", "RUNWAY_API_KEY", "KLING_API_KEY"],
    group: "gpu",
    label: "AI provider key",
  },
  {
    key: "RESEND_API_KEY",
    required: false,
    alt: ["SMTP_PASS"],
    group: "email",
    label: "Email delivery (Resend or SMTP)",
  },
  { key: "EMAIL_FROM", required: false, group: "email" },
  {
    key: "PADDLE_WEBHOOK_SECRET",
    required: provider === "paddle",
    group: "payments",
  },
  {
    key: "NEXT_PUBLIC_PADDLE_CHECKOUT_URL",
    required: false,
    alt: [
      "NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL",
      "NEXT_PUBLIC_PADDLE_TESTER_CHECKOUT_URL",
    ],
    group: "payments",
    label: "Paddle checkout URL",
    when: provider === "paddle",
  },
  {
    key: "LEMONSQUEEZY_WEBHOOK_SECRET",
    required: provider === "lemon_squeezy",
    group: "payments",
  },
  {
    key: "NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL",
    required: false,
    alt: [
      "NEXT_PUBLIC_LEMONSQUEEZY_STANDARD_CHECKOUT_URL",
      "NEXT_PUBLIC_LEMONSQUEEZY_TESTER_CHECKOUT_URL",
    ],
    group: "payments",
    label: "Lemon Squeezy checkout URL",
    when: provider === "lemon_squeezy",
  },
  {
    key: "RTAS_GENERATION_WEBHOOK_SECRET",
    required: false,
    alt: ["AI_BACKEND_SECRET"],
    group: "gpu",
    label: "Generation webhook secret",
  },
];

let failed = 0;
const byGroup = {
  secrets: [],
  payments: [],
  email: [],
  gpu: [],
};

console.log("RTAS production readiness\n");
console.log(`Payment provider: ${provider}`);
console.log(`Env file: ${existsSync(envPath) ? envPath : "(process.env only)"}\n`);

for (const check of checks) {
  if (check.when === false) continue;
  const label = check.label || check.key;
  const present =
    has(check.key) || (check.alt ?? []).some((k) => has(k));
  const required = check.required === true;
  const status = present ? "ok" : required ? "FAIL" : "warn";
  if (status === "FAIL") failed += 1;
  const line = `[${status}] ${label}`;
  byGroup[check.group].push(line);
  console.log(line);
}

console.log("\n--- Summary ---");
for (const [group, lines] of Object.entries(byGroup)) {
  console.log(`\n${group.toUpperCase()}`);
  for (const line of lines) console.log(`  ${line}`);
}

if (failed > 0) {
  console.error(
    `\n${failed} required production setting(s) missing. Configure before commercial launch.`
  );
  if (process.env.RTAS_ALLOW_INCOMPLETE_ENV === "1") {
    console.warn("RTAS_ALLOW_INCOMPLETE_ENV=1 — exiting 0 for local CI.");
    process.exit(0);
  }
  process.exit(1);
}

console.log("\nAll required production settings present.");
process.exit(0);
