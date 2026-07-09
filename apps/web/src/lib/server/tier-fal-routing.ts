import {
  isPaidTier,
  type SubscriptionTier,
  type UserProfile,
} from "@rtas/shared";

export const BILLING_REQUIRED_MESSAGE =
  "Payment required: a valid paid plan, active subscription, and credits are required for cloud rendering.";

export type BillingGateResult =
  | { ok: true }
  | { ok: false; status: 402; message: string };

function normalizeTier(tier: string | undefined | null): SubscriptionTier | null {
  const value = (tier ?? "").trim().toLowerCase();
  if (value === "tester" || value === "standard" || value === "premium") {
    return value;
  }
  return null;
}

/**
 * Server-side billing gate before proxying live Fal renders.
 * Preview and free-trial paths are exempt.
 */
export function assertBillingForFalLive(
  profile: Pick<
    UserProfile,
    "tier" | "credits" | "subscriptionActive" | "creditsExpireAt"
  >,
  options: { previewOnly: boolean; useFreeTrial: boolean }
): BillingGateResult {
  if (options.previewOnly || options.useFreeTrial) {
    return { ok: true };
  }

  const tier = normalizeTier(profile.tier);
  if (!tier || !isPaidTier(tier)) {
    return { ok: false, status: 402, message: BILLING_REQUIRED_MESSAGE };
  }

  if (profile.creditsExpireAt) {
    const expired = new Date(profile.creditsExpireAt) < new Date();
    if (expired && profile.credits > 0) {
      return { ok: false, status: 402, message: BILLING_REQUIRED_MESSAGE };
    }
  }

  if (!Number.isFinite(profile.credits) || profile.credits <= 0) {
    return { ok: false, status: 402, message: BILLING_REQUIRED_MESSAGE };
  }

  if (
    (tier === "standard" || tier === "premium") &&
    !profile.subscriptionActive
  ) {
    return { ok: false, status: 402, message: BILLING_REQUIRED_MESSAGE };
  }

  return { ok: true };
}

/** Authoritative profile snapshot for FastAPI — never trust client-supplied billing. */
export function profileToGenerateSnapshot(profile: UserProfile) {
  return {
    subscriptionActive: profile.subscriptionActive,
    credits: profile.credits,
    tier: profile.tier,
    freeTrialUsed: profile.freeTrialUsed,
    hasUsedFreeTrial: profile.hasUsedFreeTrial,
  };
}
