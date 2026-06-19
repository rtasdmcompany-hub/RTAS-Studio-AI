import { promises as fs } from "fs";
import path from "path";
import type { PaidPlanType } from "@rtas/shared";

const DATA_DIR = path.join(process.cwd(), ".data");
const LEDGER_FILE = path.join(DATA_DIR, "fal-ledger.json");

export type FalLedgerEntry = {
  id: string;
  paymentId: string;
  userId: string;
  planType: PaidPlanType;
  creditsGranted: number;
  falBudgetUsd: number;
  createdAt: string;
};

export type FalBalanceSnapshot = {
  balanceUsd: number | null;
  requiredPoolUsd: number;
  activePremium: number;
  activeTester: number;
  shortfallUsd: number;
  checkedAt: string;
  topUpRecommendedUsd: number;
  alertMessage?: string;
};

type FalLedgerFile = {
  entries: FalLedgerEntry[];
  lastSnapshot?: FalBalanceSnapshot;
};

async function ensureDataDir() {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function readLedger(): Promise<FalLedgerFile> {
  try {
    const raw = await fs.readFile(LEDGER_FILE, "utf-8");
    return JSON.parse(raw) as FalLedgerFile;
  } catch {
    return { entries: [] };
  }
}

async function writeLedger(data: FalLedgerFile) {
  await ensureDataDir();
  await fs.writeFile(LEDGER_FILE, JSON.stringify(data, null, 2), "utf-8");
}

export async function recordFalLedgerEntry(
  entry: Omit<FalLedgerEntry, "id" | "createdAt"> & { id?: string }
): Promise<FalLedgerEntry | null> {
  const ledger = await readLedger();
  const existing = ledger.entries.find((e) => e.paymentId === entry.paymentId);
  if (existing) return null;

  const row: FalLedgerEntry = {
    id: entry.id ?? `fal-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: new Date().toISOString(),
    paymentId: entry.paymentId,
    userId: entry.userId,
    planType: entry.planType,
    creditsGranted: entry.creditsGranted,
    falBudgetUsd: entry.falBudgetUsd,
  };
  ledger.entries.push(row);
  await writeLedger(ledger);
  return row;
}

export async function saveFalBalanceSnapshot(snapshot: FalBalanceSnapshot) {
  const ledger = await readLedger();
  ledger.lastSnapshot = snapshot;
  await writeLedger(ledger);
}

export async function getFalLedgerSummary(): Promise<{
  entries: FalLedgerEntry[];
  lastSnapshot?: FalBalanceSnapshot;
  totalReservedUsd: number;
}> {
  const ledger = await readLedger();
  const totalReservedUsd = ledger.entries.reduce((sum, e) => sum + e.falBudgetUsd, 0);
  return {
    entries: ledger.entries.slice(-50).reverse(),
    lastSnapshot: ledger.lastSnapshot,
    totalReservedUsd: Math.round(totalReservedUsd * 100) / 100,
  };
}
