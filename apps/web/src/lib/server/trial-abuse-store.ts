import { promises as fs } from "fs";
import path from "path";

import { getServerDataDir } from "@/lib/server/data-dir";

const DATA_DIR = getServerDataDir();
const TRIAL_CLAIMS_FILE = path.join(DATA_DIR, "trial-claims.json");

export const FREE_TRIAL_ABUSE_MESSAGE =
  "Free trial limit reached for this device/network. Please upgrade to the Premium Plan to continue.";

export interface TrialClaimRecord {
  userId: string;
  ipAddress: string;
  deviceFingerprint: string;
  claimedAt: string;
}

async function ensureDataDir() {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function readClaims(): Promise<TrialClaimRecord[]> {
  try {
    const raw = await fs.readFile(TRIAL_CLAIMS_FILE, "utf-8");
    const parsed = JSON.parse(raw) as { claims?: TrialClaimRecord[] };
    return Array.isArray(parsed.claims) ? parsed.claims : [];
  } catch {
    return [];
  }
}

async function writeClaims(claims: TrialClaimRecord[]) {
  await ensureDataDir();
  await fs.writeFile(
    TRIAL_CLAIMS_FILE,
    JSON.stringify({ claims }, null, 2),
    "utf-8"
  );
}

export function getTrialClaimsFilePath(): string {
  return TRIAL_CLAIMS_FILE;
}

export async function isFreeTrialBlocked(params: {
  userId: string;
  ipAddress: string;
  deviceFingerprint: string;
  accountTrialUsed: boolean;
}): Promise<{ blocked: boolean; reason?: "account" | "ip" | "device" }> {
  const ip = params.ipAddress.trim();
  const fingerprint = params.deviceFingerprint.trim();

  if (params.accountTrialUsed) {
    return { blocked: true, reason: "account" };
  }

  const claims = await readClaims();
  if (ip && claims.some((c) => c.ipAddress === ip)) {
    return { blocked: true, reason: "ip" };
  }
  if (fingerprint && claims.some((c) => c.deviceFingerprint === fingerprint)) {
    return { blocked: true, reason: "device" };
  }

  return { blocked: false };
}

export async function recordFreeTrialClaim(params: {
  userId: string;
  ipAddress: string;
  deviceFingerprint: string;
}): Promise<void> {
  const claims = await readClaims();
  const ip = params.ipAddress.trim();
  const fingerprint = params.deviceFingerprint.trim();

  const exists = claims.some(
    (c) =>
      c.userId === params.userId ||
      (ip && c.ipAddress === ip) ||
      (fingerprint && c.deviceFingerprint === fingerprint)
  );
  if (exists) return;

  claims.push({
    userId: params.userId,
    ipAddress: ip,
    deviceFingerprint: fingerprint,
    claimedAt: new Date().toISOString(),
  });
  await writeClaims(claims);
}
