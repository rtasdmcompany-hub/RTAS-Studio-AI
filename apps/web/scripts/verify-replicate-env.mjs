#!/usr/bin/env node
/**
 * Cross-check REPLICATE_API_TOKEN in frontend .env.local and backend .env.
 * Runs backend Python verifier when token is present.
 */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const webEnvPath = join(webRoot, ".env.local");
const backendEnvPath = join(webRoot, "..", "backend", ".env");
const backendScript = join(webRoot, "..", "backend", "scripts", "verify_replicate_env.py");

function parseEnvFile(raw) {
  const vars = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    vars[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
  }
  return vars;
}

console.log("RTAS Replicate env verification");
console.log("");

let backendToken = "";
if (existsSync(backendEnvPath)) {
  backendToken = parseEnvFile(readFileSync(backendEnvPath, "utf8")).REPLICATE_API_TOKEN ?? "";
} else {
  console.error("[fail] Missing:", backendEnvPath);
  process.exit(1);
}

if (!backendToken) {
  console.log("[info] REPLICATE_API_TOKEN not set in apps/backend/.env");
  console.log("[info] Paste your token on line 11:");
  console.log("       REPLICATE_API_TOKEN=r8_YourTokenHere");
  process.exit(0);
}

console.log("[ok]   Backend token present in apps/backend/.env line 11");

if (existsSync(webEnvPath)) {
  const webToken = parseEnvFile(readFileSync(webEnvPath, "utf8")).REPLICATE_API_TOKEN ?? "";
  if (webToken) {
    console.log("[ok]   Frontend token present in apps/web/.env.local");
  } else {
    console.warn("[warn] Frontend REPLICATE_API_TOKEN empty (optional — backend drives generation)");
  }
}

console.log("");
console.log("Calling Replicate API to validate token…");

const py = spawnSync("python", [backendScript], {
  cwd: join(webRoot, "..", "backend"),
  encoding: "utf8",
});

if (py.stdout) process.stdout.write(py.stdout);
if (py.stderr) process.stderr.write(py.stderr);
process.exit(py.status ?? 1);
