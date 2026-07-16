/**
 * Schema presence check against DATABASE_URL from .env.local
 * Does not print secrets.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { PrismaClient } from "@prisma/client";

function loadDatabaseUrl() {
  const envPath = resolve(process.cwd(), ".env.local");
  const text = readFileSync(envPath, "utf8");
  const line = text.split(/\r?\n/).find((l) => l.startsWith("DATABASE_URL="));
  if (!line) throw new Error("DATABASE_URL missing");
  return line.slice("DATABASE_URL=".length).trim();
}

const url = loadDatabaseUrl();
const prisma = new PrismaClient({ datasources: { db: { url } } });

const checks = {
  hasProjectTable: false,
  hasProgressPercent: false,
  hasCreditsDebited: false,
  hasProjectId: false,
  hasPreparingEnum: false,
  hasCancelledEnum: false,
  reachable: false,
  error: null,
};

try {
  await prisma.$queryRawUnsafe(`SELECT 1`);
  checks.reachable = true;

  const tables = await prisma.$queryRawUnsafe(
    `SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema='public' AND table_name='Project'
    ) AS ok`
  );
  checks.hasProjectTable = Boolean(tables?.[0]?.ok);

  const cols = await prisma.$queryRawUnsafe(
    `SELECT column_name FROM information_schema.columns
     WHERE table_schema='public' AND table_name='GenerationJob'`
  );
  const names = new Set((cols || []).map((r) => r.column_name));
  checks.hasProgressPercent = names.has("progressPercent");
  checks.hasCreditsDebited = names.has("creditsDebited");
  checks.hasProjectId = names.has("projectId");

  const enums = await prisma.$queryRawUnsafe(
    `SELECT e.enumlabel AS label
     FROM pg_enum e
     JOIN pg_type t ON e.enumtypid = t.oid
     WHERE t.typname = 'GenerationJobStatus'`
  );
  const labels = new Set((enums || []).map((r) => r.label));
  checks.hasPreparingEnum = labels.has("PREPARING");
  checks.hasCancelledEnum = labels.has("CANCELLED");
} catch (err) {
  checks.error = err instanceof Error ? err.message : String(err);
} finally {
  await prisma.$disconnect();
}

console.log(JSON.stringify(checks, null, 2));
process.exit(checks.reachable && !checks.error ? 0 : 2);
