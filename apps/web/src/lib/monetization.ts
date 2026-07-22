import {
  creditsForDuration,
  isPaidTier,
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  rolloverCredits,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  shouldConfirmEarlyResubscribe,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
  type PaymentProvider,
} from "@rtas/shared";
import type { UserProfile } from "@rtas/shared";

/** Active MoR provider for checkout (configure in .env) */
export function getActivePaymentProvider(): PaymentProvider | null {
  if (process.env.NEXT_PUBLIC_PAYMENT_PROVIDER === "paddle") return "paddle";
  if (process.env.NEXT_PUBLIC_PAYMENT_PROVIDER === "lemon_squeezy") {
    return "lemon_squeezy";
  }
  return null;
}

export function standardCreditsGrant(): number {
  return STANDARD_CREDITS;
}

export function premiumCreditsGrant(): number {
  return PREMIUM_CREDITS;
}

function creditsNotExpired(profile: UserProfile): boolean {
  if (!profile.creditsExpireAt) return true;
  return new Date(profile.creditsExpireAt) > new Date();
}

/** User has enough paid credits for the requested duration */
export function hasPremiumAccess(
  profile: UserProfile,
  durationSeconds: number
): boolean {
  const required = creditsForDuration(durationSeconds);
  if (!creditsNotExpired(profile)) return false;
  if (isPaidTier(profile.tier) && profile.credits >= required) {
    return true;
  }
  return profile.subscriptionActive && profile.credits >= required;
}

export function hasTesterAccess(profile: UserProfile): boolean {
  return (
    profile.tier === "tester" &&
    profile.credits > 0 &&
    creditsNotExpired(profile)
  );
}

/**
 * Legacy free preview — disabled. Entry plan is Tester ($5 / 30s).
 */
export function canUseFreeTrial(
  _profile: UserProfile,
  _durationSeconds: number
): boolean {
  return false;
}

/** Block generation — show recharge popup */
export function shouldShowPaywall(
  profile: UserProfile,
  durationSeconds: number
): boolean {
  if (hasPremiumAccess(profile, durationSeconds)) return false;
  if (hasZeroCredits(profile)) return true;
  if (canUseFreeTrial(profile, durationSeconds)) return false;
  const required = creditsForDuration(durationSeconds);
  return profile.credits < required;
}

export function hasZeroCredits(profile: UserProfile): boolean {
  if (!creditsNotExpired(profile)) return true;
  return profile.credits <= 0;
}

export const FREE_TRIAL_ABUSE_MESSAGE =
  "Free trial limit reached for this device/network. Please get the Tester or Standard plan to continue.";

export { shouldConfirmEarlyResubscribe, rolloverCredits };

/** Header / pill label — always reflects the real credit balance. */
export function creditsLabel(profile: UserProfile): string {
  const balance = Math.max(0, profile.credits);
  if (profile.tier === "tester") {
    const days = profile.creditsExpireAt
      ? Math.max(
          0,
          Math.ceil(
            (new Date(profile.creditsExpireAt).getTime() - Date.now()) / 86400000
          )
        )
      : TESTER_DURATION_DAYS;
    return `${balance} (Tester · ${days}d left)`;
  }
  if (profile.tier === "standard") {
    return `${balance} (Standard)`;
  }
  if (profile.tier === "premium") {
    return `${balance} (Premium 4K)`;
  }
  if (balance > 0) {
    return `${balance}`;
  }
  return `0 · Tester $${TESTER_PRICE_USD}`;
}

export function paywallReasonMessage(profile: UserProfile, creditsRequired: number): string {
  if (hasZeroCredits(profile)) {
    return `You have no credits. Please recharge your account — plans start at $${TESTER_PRICE_USD} Tester (${TESTER_CREDITS}s), $${STANDARD_PRICE_USD}/mo Standard (${STANDARD_CREDITS}s), or $${PREMIUM_PRICE_USD}/mo Premium 4K (${PREMIUM_CREDITS}s).`;
  }
  return `This video needs ${creditsRequired} credits but you only have ${profile.credits}. Please recharge to continue.`;
}
