#!/usr/bin/env node
/**
 * Validate apps/web/.env.local structure (required keys, format, no quotes).
 * Google credentials optional — reports placeholder vs configured state.
 */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const envPath = join(webRoot, ".env.local");

const REQUIRED_KEYS = [
  "NEXTAUTH_URL",
  "NEXTAUTH_SECRET",
  "GOOGLE_CLIENT_ID",
  "GOOGLE_CLIENT_SECRET",
  "NEXT_PUBLIC_GOOGLE_AUTH_ENABLED",
  "NEXT_PUBLIC_APP_URL",
  "NEXT_PUBLIC_FASTAPI_URL",
];

function parseEnvFile(raw) {
  const vars = {};
  const lines = raw.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) {
      console.warn(`[warn] Line ${i + 1}: not KEY=value — ${trimmed.slice(0, 40)}`);
      continue;
    }
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      console.warn(`[warn] ${key} has wrapping quotes — remove them`);
      val = val.slice(1, -1);
    }
    if (key in vars) console.warn(`[warn] Duplicate key: ${key}`);
    vars[key] = val;
  }
  return vars;
}

if (!existsSync(envPath)) {
  console.error("[fail] Missing:", envPath);
  console.error("Run: npm run setup:env");
  process.exit(1);
}

const raw = readFileSync(envPath, "utf8");
const vars = parseEnvFile(raw);
let failed = false;

console.log("RTAS .env.local structure check");
console.log("  Path:", envPath);
console.log("");

for (const key of REQUIRED_KEYS) {
  if (!(key in vars)) {
    console.error(`[fail] Missing required key: ${key}`);
    failed = true;
  } else {
    console.log(`[ok]   ${key}`);
  }
}

const nextAuthUrl = vars.NEXTAUTH_URL ?? "";
const secret = vars.NEXTAUTH_SECRET ?? "";
if (secret.length < 32) {
  console.warn("[warn] NEXTAUTH_SECRET should be at least 32 chars (run npm run setup:env)");
}
if (!/^https?:\/\//.test(nextAuthUrl)) {
  console.warn("[warn] NEXTAUTH_URL should be a full URL (http://localhost:3000)");
}

const id = vars.GOOGLE_CLIENT_ID ?? "";
const googleSecret = vars.GOOGLE_CLIENT_SECRET ?? "";
const callback = `${nextAuthUrl.replace(/\/$/, "")}/api/auth/callback/google`;

console.log("");
console.log("OAuth callback (register in Google Cloud):");
console.log(" ", callback);
console.log("");

if (!id && !googleSecret) {
  console.log("[info] Google OAuth placeholders empty — email/password auth works.");
  console.log("[info] Paste GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, then restart dev server.");
} else if (id && googleSecret) {
  const idOk = /^[\w-]+\.apps\.googleusercontent\.com$/.test(id);
  const secretOk = googleSecret.startsWith("GOCSPX-") && googleSecret.length >= 20;
  console.log("  GOOGLE_CLIENT_ID length:", id.length, idOk ? "(format ok)" : "(INVALID format)");
  console.log("  GOOGLE_CLIENT_SECRET length:", googleSecret.length, secretOk ? "(format ok)" : "(INVALID format)");
  if (!idOk || !secretOk) failed = true;
} else {
  console.error("[fail] Set BOTH GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, or leave both empty.");
  failed = true;
}

console.log("");
if (failed) {
  console.error("[fail] Fix issues above and run: npm run verify:env");
  process.exit(1);
}

const backendEnvPath = join(webRoot, "..", "backend", ".env");
const replicateWeb = vars.REPLICATE_API_TOKEN ?? "";
let replicateBackend = "";

console.log("");
console.log("Replicate (live cloud video generation):");
console.log("  Frontend .env.local REPLICATE_API_TOKEN:", replicateWeb ? "(set)" : "(empty — UI flag only)");
console.log("  Backend .env (required for generation):", backendEnvPath);

if (existsSync(backendEnvPath)) {
  const backendVars = parseEnvFile(readFileSync(backendEnvPath, "utf8"));
  replicateBackend = backendVars.REPLICATE_API_TOKEN ?? "";
  if (replicateBackend) {
    console.log("  [ok]   Backend REPLICATE_API_TOKEN is set");
    console.log("  [info] Verify with: cd apps/backend && python scripts/verify_replicate_env.py");
  } else {
    console.log("  [info] Backend REPLICATE_API_TOKEN empty — simulation mode");
    console.log("  [info] Paste token in apps/backend/.env line 11:");
    console.log("         REPLICATE_API_TOKEN=r8_YourTokenHere");
  }
} else {
  console.warn("  [warn] Missing backend .env — run backend setup");
}

console.log("");
console.log("[ok] .env.local structure is valid.");
