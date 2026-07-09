#!/usr/bin/env node
/** Print presence/length of critical env keys — never prints values. */
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const envPath = join(dirname(fileURLToPath(import.meta.url)), "..", ".env.local");
if (!existsSync(envPath)) {
  console.error("Missing .env.local");
  process.exit(1);
}

const map = {};
for (const line of readFileSync(envPath, "utf8").split(/\r?\n/)) {
  const s = line.trim();
  if (!s || s.startsWith("#")) continue;
  const i = s.indexOf("=");
  if (i <= 0) continue;
  let v = s.slice(i + 1).trim();
  if (
    (v.startsWith('"') && v.endsWith('"')) ||
    (v.startsWith("'") && v.endsWith("'"))
  ) {
    v = v.slice(1, -1);
  }
  map[s.slice(0, i).trim()] = v;
}

const keys = [
  "PADDLE_WEBHOOK_SECRET",
  "NEXT_PUBLIC_PADDLE_CHECKOUT_URL",
  "NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL",
  "RESEND_API_KEY",
  "FAL_KEY",
  "FASTAPI_URL",
  "DATABASE_URL",
  "VERCEL_TOKEN",
  "NEXTAUTH_URL",
  "NEXT_PUBLIC_APP_URL",
  "KV_REST_API_URL",
  "UPSTASH_REDIS_REST_URL",
];

for (const k of keys) {
  const v = map[k] || "";
  if (!v) {
    console.log(`${k}: EMPTY`);
  } else {
    console.log(`${k}: present len=${v.length}`);
  }
}
