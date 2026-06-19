import {
  creditsForDuration,
  FREE_TRIAL_DURATION_SECONDS,
  isPaidTier,
  TESTER_CREDITS,
  type UserProfile,
} from "@rtas/shared";

export type DurationValidation = {
  allowed: boolean;
  maxAllowedSeconds: number;
  message?: string;
  reason?: "tester_cap" | "insufficient_credits" | "need_plan";
};

/** Max selectable length for the current account (1 credit = 1 second). */
export function getMaxVideoDurationSeconds(profile: UserProfile): number {
  if (profile.tier === "tester") {
    return Math.min(TESTER_CREDITS, Math.max(0, profile.credits));
  }
  if (profile.tier === "standard" || profile.tier === "premium") {
    return Math.max(0, profile.credits);
  }
  if (!profile.freeTrialUsed && !profile.hasUsedFreeTrial) {
    return FREE_TRIAL_DURATION_SECONDS;
  }
  return 0;
}

export function validateDurationSelection(
  profile: UserProfile,
  durationSeconds: number
): DurationValidation {
  const maxAllowed = getMaxVideoDurationSeconds(profile);
  const required = creditsForDuration(durationSeconds);

  if (profile.tier === "tester" && durationSeconds > TESTER_CREDITS) {
    return {
      allowed: false,
      maxAllowedSeconds: Math.min(TESTER_CREDITS, profile.credits),
      reason: "tester_cap",
      message: `Tester plan allows up to ${TESTER_CREDITS} seconds per account. Recharge or upgrade to Standard ($89/mo) for longer videos.`,
    };
  }

  if (durationSeconds > maxAllowed) {
    if (profile.tier === "tester" || isPaidTier(profile.tier)) {
      return {
        allowed: false,
        maxAllowedSeconds: maxAllowed,
        reason: "insufficient_credits",
        message:
          maxAllowed <= 0
            ? "You have no credits left. Please recharge your account to select a video length."
            : `You only have ${maxAllowed} credits (${maxAllowed}s) remaining. This length needs ${required}s — please recharge your account.`,
      };
    }
    return {
      allowed: false,
      maxAllowedSeconds: maxAllowed,
      reason: "need_plan",
      message:
        "Please recharge your account — plans start at $5 Tester (30 seconds).",
    };
  }

  return { allowed: true, maxAllowedSeconds: maxAllowed };
}

export function filterDurationOptionValues(
  optionValues: string[],
  maxAllowedSeconds: number
): string[] {
  return optionValues.filter((value) => {
    const secs = Number.parseInt(value, 10);
    return Number.isFinite(secs) && secs <= maxAllowedSeconds;
  });
}
