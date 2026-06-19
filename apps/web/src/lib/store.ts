import type { GeneratedVideo, UserProfile } from "@rtas/shared";
import {
  PREMIUM_CREDITS,
  STANDARD_CREDITS,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  type PaidPlanType,
} from "@rtas/shared";

const PROFILE_KEY = "rtas_profile";
const VIDEOS_KEY = "rtas_videos";

export function getDefaultProfile(): UserProfile {
  return {
    id: "local-user",
    email: "user@example.com",
    name: "Creator",
    tier: "free",
    freeTrialUsed: false,
    hasUsedFreeTrial: false,
    ipAddress: null,
    deviceFingerprint: null,
    credits: 0,
    creditsExpireAt: null,
    subscriptionActive: false,
    subscriptionRenewsAt: null,
    previewSkipsRemaining: 3,
    createdAt: new Date().toISOString(),
  };
}

export function loadProfile(): UserProfile {
  if (typeof window === "undefined") return getDefaultProfile();
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return getDefaultProfile();
    const merged = { ...getDefaultProfile(), ...JSON.parse(raw) };
    return capCreditsForTier(applyCreditExpiry(merged));
  } catch {
    return getDefaultProfile();
  }
}

/** Monthly plans grant a fixed bucket — cap corrupted/stacked local values */
export function capCreditsForTier(profile: UserProfile): UserProfile {
  const cap =
    profile.tier === "tester"
      ? TESTER_CREDITS
      : profile.tier === "standard"
        ? STANDARD_CREDITS
        : profile.tier === "premium"
          ? PREMIUM_CREDITS
          : null;
  if (cap == null || profile.credits <= cap) return profile;
  return {
    ...profile,
    credits: cap,
    updatedAt: new Date().toISOString(),
  };
}

export function saveProfile(profile: UserProfile): void {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function loadVideos(): GeneratedVideo[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(VIDEOS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveVideos(videos: GeneratedVideo[]): void {
  localStorage.setItem(VIDEOS_KEY, JSON.stringify(videos));
}

export function loadVideosForUser(userId: string): GeneratedVideo[] {
  return loadVideos().filter((v) => v.userId === userId);
}

/** Persist one user's list while keeping other users' entries intact. */
export function saveVideosForUser(
  userId: string,
  userVideos: GeneratedVideo[]
): void {
  const others = loadVideos().filter((v) => v.userId !== userId);
  saveVideos([...userVideos, ...others]);
}

export function activateTesterSubscription(profile: UserProfile): UserProfile {
  const now = new Date();
  const end = new Date(now);
  end.setDate(end.getDate() + TESTER_DURATION_DAYS);

  return {
    ...profile,
    tier: "tester",
    subscriptionActive: true,
    credits: TESTER_CREDITS,
    creditsExpireAt: end.toISOString(),
    subscriptionRenewsAt: null,
    hasUsedFreeTrial: true,
    freeTrialUsed: true,
    paymentProvider: profile.paymentProvider ?? "manual",
    updatedAt: new Date().toISOString(),
  };
}

function activateMonthlyPlan(
  profile: UserProfile,
  tier: "standard" | "premium",
  grant: number,
  options?: { rolloverRemaining?: boolean }
): UserProfile {
  const now = new Date();
  const end = new Date(now);
  end.setMonth(end.getMonth() + 1);

  let credits = grant;
  if (options?.rolloverRemaining) {
    const hasUnexpired =
      profile.credits > 0 &&
      profile.creditsExpireAt &&
      new Date(profile.creditsExpireAt) > now;
    const sameTier = profile.tier === tier;
    if (hasUnexpired && sameTier && profile.subscriptionActive) {
      credits = profile.credits + grant;
    }
  }

  return {
    ...profile,
    tier,
    subscriptionActive: true,
    credits,
    creditsExpireAt: end.toISOString(),
    subscriptionRenewsAt: end.toISOString(),
    paymentProvider: profile.paymentProvider ?? "manual",
    updatedAt: new Date().toISOString(),
  };
}

export function activateStandardSubscription(
  profile: UserProfile,
  options?: { rolloverRemaining?: boolean }
): UserProfile {
  return activateMonthlyPlan(profile, "standard", STANDARD_CREDITS, options);
}

export function activatePremiumSubscription(
  profile: UserProfile,
  options?: { rolloverRemaining?: boolean }
): UserProfile {
  return activateMonthlyPlan(profile, "premium", PREMIUM_CREDITS, options);
}

/** @deprecated Use activateStandardSubscription */
export function activateSubscription(profile: UserProfile): UserProfile {
  return activateStandardSubscription(profile);
}

export function activatePlan(
  profile: UserProfile,
  plan: PaidPlanType = "standard",
  options?: { rolloverRemaining?: boolean }
): UserProfile {
  if (plan === "tester") return activateTesterSubscription(profile);
  if (plan === "premium") return activatePremiumSubscription(profile, options);
  return activateStandardSubscription(profile, options);
}

/** Merge server webhook state into client profile */
/** Expire unused credits at billing period end */
export function applyCreditExpiry(profile: UserProfile): UserProfile {
  if (!profile.creditsExpireAt || profile.credits <= 0) return profile;
  if (new Date(profile.creditsExpireAt) >= new Date()) return profile;
  return {
    ...profile,
    credits: 0,
    tier: "free",
    subscriptionActive: false,
    updatedAt: new Date().toISOString(),
  };
}

export function mergeServerProfile(
  local: UserProfile,
  server: UserProfile
): UserProfile {
  const serverPaid =
    server.subscriptionActive ||
    server.tier === "premium" ||
    server.tier === "standard" ||
    server.tier === "tester" ||
    server.credits > 0;
  if (!serverPaid) return local;
  return {
    ...local,
    ...server,
    id: local.id,
    email: local.email || server.email,
    tier:
      server.tier === "premium" ||
      server.tier === "standard" ||
      server.tier === "tester"
        ? server.tier
        : local.tier,
    subscriptionActive: server.subscriptionActive,
    credits: server.credits,
    creditsExpireAt: server.creditsExpireAt,
    subscriptionRenewsAt: server.subscriptionRenewsAt,
    paymentProvider: server.paymentProvider ?? local.paymentProvider,
    hasUsedFreeTrial:
      server.hasUsedFreeTrial ?? server.freeTrialUsed ?? local.hasUsedFreeTrial,
    freeTrialUsed:
      server.freeTrialUsed ?? server.hasUsedFreeTrial ?? local.freeTrialUsed,
  };
}
