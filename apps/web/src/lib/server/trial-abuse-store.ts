import { readJsonDocument, writeJsonDocument } from "@/lib/server/persistent-store";

const STORE_NAME = "trial-claims";

export const FREE_TRIAL_ABUSE_MESSAGE =
  "Free trial limit reached for this device/network. Please upgrade to the Premium Plan to continue.";

export interface TrialClaimRecord {
  userId: string;
  ipAddress: string;
  deviceFingerprint: string;
  claimedAt: string;
}

type TrialClaimsFile = { claims: TrialClaimRecord[] };

async function readClaims(): Promise<TrialClaimRecord[]> {
  const parsed = await readJsonDocument<TrialClaimsFile>(STORE_NAME, { claims: [] });
  return Array.isArray(parsed.claims) ? parsed.claims : [];
}

async function writeClaims(claims: TrialClaimRecord[]) {
  await writeJsonDocument(STORE_NAME, { claims });
}

export function getTrialClaimsFilePath(): string {
  return STORE_NAME;
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
