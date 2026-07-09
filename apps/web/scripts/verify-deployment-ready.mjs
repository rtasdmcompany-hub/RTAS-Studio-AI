#!/usr/bin/env node
/**
 * Deployment-readiness gate (no production credentials required).
 * Verifies templates, docs, health routes, CI, and local quality scripts exist.
 * Optionally runs lint/typecheck/smoke/build when --full is passed.
 *
 * Exit 0 = engineering deployment-ready.
 * Exit 1 = missing readiness artifacts.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = join(webRoot, "..", "..");
const full = process.argv.includes("--full");

let failed = 0;

function pass(name) {
  console.log(`[pass] ${name}`);
}
function fail(name, detail = "") {
  failed += 1;
  console.error(`[FAIL] ${name}${detail ? ` — ${detail}` : ""}`);
}

function mustExist(relFromRepo, label) {
  const p = join(repoRoot, relFromRepo);
  if (existsSync(p)) pass(label || relFromRepo);
  else fail(label || relFromRepo, "missing");
}

function fileContains(relFromRepo, needle, label) {
  const p = join(repoRoot, relFromRepo);
  if (!existsSync(p)) {
    fail(label, "file missing");
    return;
  }
  const text = readFileSync(p, "utf8");
  if (text.includes(needle)) pass(label);
  else fail(label, `expected to contain: ${needle}`);
}

console.log("RTAS deployment-readiness verification\n");

// --- Templates ---
mustExist("apps/web/.env.example", "apps/web/.env.example");
mustExist(
  "apps/web/.env.production.example",
  "apps/web/.env.production.example"
);
mustExist("apps/backend/.env.example", "apps/backend/.env.example");
mustExist(".env.example", "root .env.example");

fileContains(
  "apps/web/.env.production.example",
  "REPLACE_APP_DOMAIN",
  "production template uses domain placeholders"
);
fileContains(
  "apps/web/.env.production.example",
  "NEXTAUTH_SECRET",
  "production template includes NEXTAUTH_SECRET"
);
fileContains(
  "apps/web/.env.production.example",
  "PADDLE_WEBHOOK_SECRET",
  "production template includes Paddle webhook"
);

// --- Docs ---
const docs = [
  "docs/DEPLOYMENT.md",
  "docs/PRODUCTION.md",
  "docs/SECURITY.md",
  "docs/BACKUP.md",
  "docs/RECOVERY.md",
  "docs/OPERATIONS.md",
  "docs/ENVIRONMENT.md",
  "docs/INFRASTRUCTURE.md",
  "docs/RELEASE-CHECKLIST.md",
  "docs/DEPLOYMENT-READY-REPORT.md",
  "DEPLOYMENT.md",
  "PRODUCTION.md",
  "SECURITY.md",
  "BACKUP.md",
  "RECOVERY.md",
  "OPERATIONS.md",
  "ENVIRONMENT.md",
];
for (const d of docs) mustExist(d, d);

// --- Health / observability ---
mustExist(
  "apps/web/src/app/api/health/route.ts",
  "GET /api/health route"
);
mustExist(
  "apps/web/src/app/api/ready/route.ts",
  "GET /api/ready route"
);
mustExist(
  "apps/web/src/lib/observability.ts",
  "observability hooks"
);

// --- CI / Vercel ---
mustExist(".github/workflows/ci-web.yml", "CI workflow ci-web.yml");
mustExist("vercel.json", "root vercel.json");
fileContains(
  ".github/workflows/ci-web.yml",
  "verify:production",
  "CI runs verify:production"
);
fileContains("vercel.json", "Strict-Transport-Security", "HSTS header configured");

// --- Scripts ---
mustExist(
  "apps/web/scripts/verify-production-readiness.mjs",
  "verify-production-readiness.mjs"
);
mustExist(
  "apps/web/scripts/probe-production-services.mjs",
  "probe-production-services.mjs"
);
mustExist(
  "apps/web/scripts/sync-vercel-env.mjs",
  "sync-vercel-env.mjs"
);
mustExist(
  "apps/web/scripts/smoke-commercial.mjs",
  "smoke-commercial.mjs"
);

// --- Required env keys documented ---
const envDoc = join(repoRoot, "docs/ENVIRONMENT.md");
if (existsSync(envDoc)) {
  const t = readFileSync(envDoc, "utf8");
  for (const key of [
    "DATABASE_URL",
    "FASTAPI_URL",
    "RESEND_API_KEY",
    "FAL_KEY",
    "PADDLE_WEBHOOK_SECRET",
  ]) {
    if (t.includes(key)) pass(`ENVIRONMENT.md documents ${key}`);
    else fail(`ENVIRONMENT.md documents ${key}`);
  }
}

if (full) {
  console.log("\n--full: running local quality gates...\n");
  const steps = [
    ["lint", ["run", "lint", "-w", "@rtas/web"]],
    ["typecheck", ["run", "typecheck", "-w", "@rtas/web"]],
    ["test", ["run", "test", "-w", "@rtas/web"]],
    [
      "verify:production",
      ["run", "verify:production", "-w", "@rtas/web"],
      { RTAS_ALLOW_INCOMPLETE_ENV: "1" },
    ],
    [
      "build",
      ["run", "build", "-w", "@rtas/web"],
      {
        RTAS_ALLOW_INCOMPLETE_ENV: "1",
        NEXT_PHASE: "phase-production-build",
        NEXTAUTH_SECRET: "ci-build-placeholder-not-for-production-use-32chars",
        NEXTAUTH_URL: "http://localhost:3000",
        NEXT_PUBLIC_APP_URL: "http://localhost:3000",
        DATABASE_URL:
          "postgresql://postgres:postgres@localhost:5432/rtas_ci?schema=public",
      },
    ],
  ];

  for (const [name, args, extraEnv] of steps) {
    const result = spawnSync("npm", args, {
      cwd: repoRoot,
      env: { ...process.env, ...(extraEnv || {}) },
      encoding: "utf8",
      shell: true,
    });
    if (result.status === 0) pass(`quality:${name}`);
    else {
      fail(`quality:${name}`, `exit ${result.status}`);
      if (result.stderr) console.error(result.stderr.slice(0, 2000));
      if (result.stdout) console.error(result.stdout.slice(-2000));
    }
  }
} else {
  console.log(
    "\nTip: run with --full to execute lint, typecheck, smoke, verify:production, build."
  );
}

console.log(
  failed
    ? `\n${failed} deployment-readiness check(s) failed.`
    : "\nDeployment-readiness checks passed (engineering gate)."
);
process.exit(failed > 0 ? 1 : 0);
