import type { UserProfile } from "@rtas/shared";
import { TESTER_CREDITS, type PaidPlanType } from "@rtas/shared";

const PROFILE_KEY = "rtas_omni_profile";

export function getDefaultProfile(): UserProfile {
  return {
    id: "local-user",
    email: "user@example.com",
    name: "Publisher",
    tier: "free",
    freeTrialUsed: false,
    hasUsedFreeTrial: false,
    credits: 0,
    creditsExpireAt: null,
    subscriptionActive: false,
    subscriptionRenewsAt: null,
    previewSkipsRemaining: 0,
    createdAt: new Date().toISOString(),
  };
}

export function loadProfile(): UserProfile {
  if (typeof window === "undefined") return getDefaultProfile();
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return getDefaultProfile();
    return { ...getDefaultProfile(), ...JSON.parse(raw) };
  } catch {
    return getDefaultProfile();
  }
}

export function saveProfile(profile: UserProfile): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function mergeServerProfile(
  local: UserProfile,
  server: Partial<UserProfile>
): UserProfile {
  return { ...local, ...server, id: server.id ?? local.id };
}

export function activatePlan(
  profile: UserProfile,
  plan: PaidPlanType
): UserProfile {
  if (plan !== "tester") return profile;
  const end = new Date();
  end.setDate(end.getDate() + 5);
  return {
    ...profile,
    tier: "tester",
    subscriptionActive: true,
    credits: TESTER_CREDITS,
    creditsExpireAt: end.toISOString(),
    hasUsedFreeTrial: true,
    freeTrialUsed: true,
    updatedAt: new Date().toISOString(),
  };
}

export function applyCreditExpiry(profile: UserProfile): UserProfile {
  if (!profile.creditsExpireAt) return profile;
  if (new Date(profile.creditsExpireAt) > new Date()) return profile;
  return {
    ...profile,
    tier: "free",
    subscriptionActive: false,
    credits: 0,
    creditsExpireAt: null,
    subscriptionRenewsAt: null,
  };
}
