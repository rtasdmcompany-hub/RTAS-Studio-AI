/**
 * Apply Prisma schema to DATABASE_URL when the DB is reachable.
 * Safe: uses prisma db push (no destructive reset).
 * Never prints connection secrets.
 */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { PrismaClient } from "@prisma/client";

function loadDatabaseUrl() {
  const envPath = resolve(process.cwd(), ".env.local");
  const text = readFileSync(envPath, "utf8");
  const line = text.split(/\r?\n/).find((l) => l.startsWith("DATABASE_URL="));
  if (!line) throw new Error("DATABASE_URL missing in .env.local");
  return line.slice("DATABASE_URL=".length).trim();
}

const url = loadDatabaseUrl();
const probe = new PrismaClient({ datasources: { db: { url } } });

try {
  await probe.$queryRawUnsafe("SELECT 1");
} catch (err) {
  const msg = err instanceof Error ? err.message : String(err);
  console.error(
    JSON.stringify({
      ok: false,
      reachable: false,
      error: msg.includes("Can't reach")
        ? "DATABASE_UNREACHABLE"
        : "DATABASE_PROBE_FAILED",
      hint: "Unpause Supabase project / fix pooler URL / allow network, then re-run: node ./scripts/apply-schema.mjs",
    })
  );
  process.exit(2);
} finally {
  await probe.$disconnect();
}

const result = spawnSync(
  "npx",
  ["prisma", "db", "push", "--schema=prisma/schema.prisma", "--skip-generate"],
  {
    env: { ...process.env, DATABASE_URL: url },
    encoding: "utf8",
    shell: true,
  }
);

console.log(result.stdout || "");
if (result.stderr) console.error(result.stderr);
if (result.status !== 0) {
  console.error(JSON.stringify({ ok: false, step: "prisma_db_push", status: result.status }));
  process.exit(result.status ?? 1);
}

console.log(JSON.stringify({ ok: true, applied: "prisma_db_push", message: "Schema synced" }));
