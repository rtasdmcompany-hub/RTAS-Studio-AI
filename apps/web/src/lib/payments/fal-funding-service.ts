import {
  DEFAULT_FAL_USD_PER_CREDIT,
  falBudgetUsdForPlan,
  requiredFalPoolUsd,
  type PaidPlanType,
  type SubscriptionActivatedPayload,
} from "@rtas/shared";
import { listActivePaidProfiles } from "@/lib/server/profile-store";
import { fetchFalAccountBalance } from "./fal-balance";
import {
  recordFalLedgerEntry,
  saveFalBalanceSnapshot,
  type FalBalanceSnapshot,
} from "@/lib/server/fal-ledger-store";

function usdPerCreditFromEnv(): number {
  const raw = process.env.FAL_USD_PER_CREDIT?.trim();
  if (!raw) return DEFAULT_FAL_USD_PER_CREDIT;
  const n = parseFloat(raw);
  return Number.isFinite(n) && n > 0 ? n : DEFAULT_FAL_USD_PER_CREDIT;
}

function bufferPercentFromEnv(): number {
  const raw = process.env.FAL_POOL_BUFFER_PERCENT?.trim();
  if (!raw) return 20;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) && n >= 0 ? n : 20;
}

export async function countActivePaidTiers(): Promise<{
  premium: number;
  tester: number;
}> {
  const profiles = await listActivePaidProfiles();
  let premium = 0;
  let tester = 0;
  const now = new Date();
  for (const p of profiles) {
    if (p.creditsExpireAt && new Date(p.creditsExpireAt) <= now) continue;
    if (p.credits <= 0) continue;
    if (p.tier === "premium" || p.tier === "standard") premium += 1;
    else if (p.tier === "tester") tester += 1;
  }
  return { premium, tester };
}

export async function evaluateFalPoolHealth(): Promise<FalBalanceSnapshot> {
  const usdPerCredit = usdPerCreditFromEnv();
  const buffer = bufferPercentFromEnv();
  const { premium, tester } = await countActivePaidTiers();
  const requiredPoolUsd = requiredFalPoolUsd(premium, tester, usdPerCredit, buffer);
  const fal = await fetchFalAccountBalance();
  const balanceUsd = fal.balanceUsd;
  const shortfallUsd =
    balanceUsd === null
      ? requiredPoolUsd
      : Math.max(0, Math.round((requiredPoolUsd - balanceUsd) * 100) / 100);

  let alertMessage: string | undefined;
  if (fal.error) {
    alertMessage = `Fal balance check failed: ${fal.error}. Enable Fal auto-recharge at https://fal.ai/dashboard/billing`;
  } else if (shortfallUsd > 0) {
    alertMessage = `Fal wallet low: need ~$${requiredPoolUsd.toFixed(2)} for ${premium} premium + ${tester} tester customers. Shortfall ~$${shortfallUsd.toFixed(2)}. Top up at https://fal.ai/dashboard/billing (enable auto-recharge).`;
  }

  const snapshot: FalBalanceSnapshot = {
    balanceUsd,
    requiredPoolUsd,
    activePremium: premium,
    activeTester: tester,
    shortfallUsd,
    checkedAt: new Date().toISOString(),
    topUpRecommendedUsd: shortfallUsd > 0 ? Math.ceil(shortfallUsd) : 0,
    alertMessage,
  };

  await saveFalBalanceSnapshot(snapshot);
  return snapshot;
}

/** After customer payment — reserve Fal budget in ledger + check pool health */
export async function processFalFundingAfterPayment(
  payload: SubscriptionActivatedPayload
): Promise<{ ledgerRecorded: boolean; snapshot: FalBalanceSnapshot }> {
  const usdPerCredit = usdPerCreditFromEnv();
  const falBudgetUsd = falBudgetUsdForPlan(payload.planType, usdPerCredit);
  const paymentId =
    payload.paymentId ||
    payload.externalSubscriptionId ||
    `pay-${payload.userId}-${Date.now()}`;

  const entry = await recordFalLedgerEntry({
    paymentId,
    userId: payload.userId,
    planType: payload.planType,
    creditsGranted: payload.creditsToGrant,
    falBudgetUsd,
  });

  const snapshot = await evaluateFalPoolHealth();

  if (snapshot.alertMessage) {
    console.warn("[RTAS Fal Funding]", snapshot.alertMessage);
  }

  return { ledgerRecorded: entry !== null, snapshot };
}
