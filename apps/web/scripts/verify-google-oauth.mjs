#!/usr/bin/env node
/** Verify Google OAuth env vars in .env.local (no secrets printed). */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const envPath = join(webRoot, ".env.local");

if (!existsSync(envPath)) {
  console.error("[fail] .env.local not found at", envPath);
  process.exit(1);
}

const raw = readFileSync(envPath, "utf8");
const vars = {};
for (const line of raw.split(/\r?\n/)) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) continue;
  const eq = trimmed.indexOf("=");
  if (eq === -1) continue;
  const key = trimmed.slice(0, eq).trim();
  let val = trimmed.slice(eq + 1).trim();
  if (
    (val.startsWith('"') && val.endsWith('"')) ||
    (val.startsWith("'") && val.endsWith("'"))
  ) {
    val = val.slice(1, -1);
  }
  vars[key] = val;
}

const id = vars.GOOGLE_CLIENT_ID ?? "";
const secret = vars.GOOGLE_CLIENT_SECRET ?? "";
const nextAuthUrl = vars.NEXTAUTH_URL ?? "http://localhost:3000";

console.log("Google OAuth env check");
console.log("  .env.local:", envPath);
console.log("  NEXTAUTH_URL:", nextAuthUrl);
console.log("  Callback URI:", `${nextAuthUrl.replace(/\/$/, "")}/api/auth/callback/google`);
console.log("  GOOGLE_CLIENT_ID length:", id.length);
console.log("  GOOGLE_CLIENT_ID suffix:", id.slice(-30));
console.log("  Valid client ID format:", /\.apps\.googleusercontent\.com$/.test(id));
console.log("  GOOGLE_CLIENT_SECRET length:", secret.length);
console.log("  Secret prefix:", secret.slice(0, 7));
console.log("  Has wrapping quotes in file:", /GOOGLE_CLIENT_(ID|SECRET)=["']/.test(raw));

const ok =
  id.length > 20 &&
  secret.length > 10 &&
  /\.apps\.googleusercontent\.com$/.test(id) &&
  secret.startsWith("GOCSPX-");

console.log(ok ? "\n[ok] Format looks valid. If Google still returns invalid_client:" : "\n[warn] Format issue detected:");
if (!ok) process.exit(1);
console.log("  1. Confirm ID + secret are from the SAME Web OAuth client in Google Cloud");
console.log("  2. Add redirect URI: http://localhost:3000/api/auth/callback/google");
console.log("  3. Add JS origin: http://localhost:3000");
console.log("  4. Restart: npm run dev (after .env.local changes)");
