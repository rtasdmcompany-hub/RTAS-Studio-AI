/** 1 credit = 1 second of generated video */
export const CREDITS_PER_SECOND = 1;

/** Standard plan — $89 / month */
export const STANDARD_CREDITS = 2000;
export const STANDARD_PRICE_USD = 89;
export const STANDARD_RATE_USD_PER_SEC = 0.02;

/** Premium cinematic plan — $249 / month */
export const PREMIUM_CREDITS = 2000;
export const PREMIUM_PRICE_USD = 249;

/** @deprecated Use STANDARD_* — kept for existing imports */
export const MONTHLY_CREDITS = STANDARD_CREDITS;
export const MONTHLY_PRICE_USD = STANDARD_PRICE_USD;

/** Tester plan — $5 / 5 days / 30 seconds */
export const TESTER_PRICE_USD = 5;
export const TESTER_CREDITS = 30;
export const TESTER_DURATION_DAYS = 5;
export const TESTER_RATE_USD_PER_SEC = 0.01;

/** @deprecated Legacy one-time preview; new users should use Tester plan */
export const FREE_TRIAL_DURATION_SECONDS = 20;

/** @deprecated Use 1 credit per second; kept for legacy references */
export const CREDITS_PER_FIVE_MINUTES = 300;

export type SubscriptionTier = "free" | "tester" | "standard" | "premium";

export function isPaidTier(tier: SubscriptionTier): boolean {
  return tier === "tester" || tier === "standard" || tier === "premium";
}

export function creditsForDuration(durationSeconds: number): number {
  return Math.max(1, Math.round(durationSeconds * CREDITS_PER_SECOND));
}

export function maxDurationForCredits(credits: number): number {
  return Math.max(0, Math.floor(credits / CREDITS_PER_SECOND));
}

export interface CreditCheckResult {
  allowed: boolean;
  creditsRequired: number;
  reason?:
    | "ok"
    | "free_trial"
    | "insufficient_credits"
    | "need_subscription"
    | "credits_expired"
    | "trial_abuse";
  useFreeTrial?: boolean;
  previewOnly?: boolean;
}

export function checkCredits(
  profile: {
    tier?: SubscriptionTier;
    freeTrialUsed: boolean;
    hasUsedFreeTrial?: boolean;
    credits: number;
    creditsExpireAt: string | null;
    subscriptionActive: boolean;
  },
  durationSeconds: number,
  options?: { allowPreviewSkip?: boolean }
): CreditCheckResult {
  const creditsRequired = creditsForDuration(durationSeconds);
  const trialUsed = profile.hasUsedFreeTrial ?? profile.freeTrialUsed;

  if (profile.creditsExpireAt) {
    const expired = new Date(profile.creditsExpireAt) < new Date();
    if (expired && profile.credits > 0) {
      return {
        allowed: false,
        creditsRequired,
        reason: "credits_expired",
      };
    }
  }

  const paidTier = isPaidTier(profile.tier ?? "free");
  if (paidTier && profile.credits >= creditsRequired) {
    return { allowed: true, creditsRequired, reason: "ok" };
  }

  if (!trialUsed && durationSeconds <= FREE_TRIAL_DURATION_SECONDS) {
    return {
      allowed: true,
      creditsRequired: 0,
      reason: "free_trial",
      useFreeTrial: true,
    };
  }

  if (profile.subscriptionActive && profile.credits >= creditsRequired) {
    return { allowed: true, creditsRequired, reason: "ok" };
  }

  if (options?.allowPreviewSkip) {
    return {
      allowed: true,
      creditsRequired: 0,
      reason: "need_subscription",
      previewOnly: true,
    };
  }

  if (!profile.subscriptionActive && profile.credits <= 0) {
    return {
      allowed: false,
      creditsRequired,
      reason: "insufficient_credits",
    };
  }

  if (!profile.subscriptionActive) {
    return {
      allowed: false,
      creditsRequired,
      reason: "need_subscription",
    };
  }

  return {
    allowed: false,
    creditsRequired,
    reason: "insufficient_credits",
  };
}

/** Early resubscribe: add remaining to new monthly grant */
export function rolloverCredits(remaining: number): number {
  return remaining + STANDARD_CREDITS;
}

export function hasUnexpiredCredits(profile: {
  credits: number;
  creditsExpireAt: string | null;
}): boolean {
  if (profile.credits <= 0 || !profile.creditsExpireAt) return false;
  return new Date(profile.creditsExpireAt) > new Date();
}

/** Active subscriber renewing before cycle end with balance remaining */
export function shouldConfirmEarlyResubscribe(profile: {
  subscriptionActive: boolean;
  tier?: SubscriptionTier;
  credits: number;
  creditsExpireAt: string | null;
}): boolean {
  const monthlyTier = profile.tier === "standard" || profile.tier === "premium";
  return (
    profile.subscriptionActive &&
    monthlyTier &&
    hasUnexpiredCredits(profile)
  );
}
