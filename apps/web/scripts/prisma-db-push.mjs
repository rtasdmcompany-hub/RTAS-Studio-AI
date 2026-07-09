#!/usr/bin/env node
/**
 * Push apps/web/prisma/schema.prisma to the database referenced by DATABASE_URL.
 * Loads DATABASE_URL from (first match): process env, .env.prisma.production,
 * .env.prisma.preview, .env.prisma, .env.local, .env
 */
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = join(__dirname, "..");
const schemaPath = resolve(webRoot, "prisma", "schema.prisma");

const ENV_CANDIDATES = [
  join(webRoot, ".env.local"),
  join(webRoot, ".env"),
  join(webRoot, ".env.prisma.production"),
  join(webRoot, ".env.prisma.preview"),
  join(webRoot, ".env.prisma"),
];

function parseEnvFile(filePath) {
  const map = new Map();
  if (!existsSync(filePath)) return map;
  const text = readFileSync(filePath, "utf8");
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

function resolveDatabaseUrl() {
  for (const file of ENV_CANDIDATES) {
    const vars = parseEnvFile(file);
    const pooler = vars.get("DATABASE_URL")?.trim();
    if (pooler) {
      console.log(`[prisma-db-push] Using DATABASE_URL from ${file}`);
      return pooler;
    }
  }

  if (process.env.DATABASE_URL?.trim()) {
    console.log("[prisma-db-push] Using DATABASE_URL from process environment");
    return process.env.DATABASE_URL.trim();
  }

  return null;
}

function runSafeStudioSync(databaseUrl) {
  const safeSqlPath = resolve(webRoot, "prisma", "safe-studio-sync.sql");
  const alignPath = resolve(webRoot, "prisma", "align-updated-at.sql");
  if (!existsSync(safeSqlPath)) {
    console.error(`[prisma-db-push] Missing safe sync script: ${safeSqlPath}`);
    return false;
  }

  const runSqlFile = (label, filePath) => {
    console.log(`[prisma-db-push] ${label}`);
    if (process.platform === "win32") {
      const ps = spawnSync(
        "powershell",
        [
          "-NoProfile",
          "-Command",
          `Get-Content -LiteralPath '${filePath.replace(/'/g, "''")}' -Raw | npx.cmd prisma db execute --stdin --schema='${schemaPath.replace(/'/g, "''")}'`,
        ],
        {
          cwd: webRoot,
          env: { ...process.env, DATABASE_URL: databaseUrl },
          stdio: "inherit",
          shell: false,
        }
      );
      return ps.status === 0;
    }

    const result = spawnSync(
      "npx",
      ["prisma", "db", "execute", "--file", filePath, `--schema=${schemaPath}`],
      {
        cwd: webRoot,
        env: { ...process.env, DATABASE_URL: databaseUrl },
        stdio: "inherit",
        shell: false,
      }
    );
    return result.status === 0;
  };

  if (!runSqlFile("Applying safe-studio-sync.sql (preserves existing tables)…", safeSqlPath)) {
    return false;
  }

  if (existsSync(alignPath)) {
    runSqlFile("Aligning updatedAt columns…", alignPath);
  }

  return true;
}

if (!existsSync(schemaPath)) {
  console.error(`[prisma-db-push] schema.prisma not found at:\n  ${schemaPath}`);
  process.exit(1);
}

console.log(`[prisma-db-push] Schema: ${schemaPath}`);

const databaseUrl = resolveDatabaseUrl();
if (!databaseUrl) {
  console.error(
    "[prisma-db-push] DATABASE_URL is not set.\n" +
      "Add it to Vercel (Production) or apps/web/.env.local, then re-run:\n" +
      "  npm run db:push --workspace=@rtas/web\n" +
      "Or:\n" +
      `  npx prisma db push --schema="${schemaPath}"`
  );
  process.exit(1);
}

const env = { ...process.env, DATABASE_URL: databaseUrl };

const push = spawnSync(
  process.platform === "win32" ? "npx.cmd" : "npx",
  ["prisma", "db", "push", `--schema=${schemaPath}`],
  {
    cwd: webRoot,
    env,
    stdio: "pipe",
    shell: false,
    encoding: "utf8",
  }
);

if (push.stdout) process.stdout.write(push.stdout);
if (push.stderr) process.stderr.write(push.stderr);

const pushOutput = `${push.stdout ?? ""}${push.stderr ?? ""}`;
if (push.status === 0) {
  console.log("[prisma-db-push] Database schema sync complete (db push).");
  process.exit(0);
}

if (existsSync(resolve(webRoot, "prisma", "safe-studio-sync.sql"))) {
  if (runSafeStudioSync(databaseUrl)) {
    spawnSync(
      process.platform === "win32" ? "npx.cmd" : "npx",
      ["prisma", "generate", `--schema=${schemaPath}`],
      { cwd: webRoot, env, stdio: "inherit", shell: false }
    );
    console.log("[prisma-db-push] Database schema sync complete (safe SQL).");
    process.exit(0);
  }
}

if (pushOutput.trim()) {
  console.error("[prisma-db-push] db push failed:", pushOutput.trim().slice(0, 500));
}

process.exit(push.status ?? 1);
