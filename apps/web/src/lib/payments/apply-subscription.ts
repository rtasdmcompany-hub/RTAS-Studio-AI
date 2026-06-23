import {
  PREMIUM_CREDITS,
  STANDARD_CREDITS,
  type SubscriptionActivatedPayload,
  type SubscriptionCancelledPayload,
  type UserProfile,
} from "@rtas/shared";
import {
  getServerProfile,
  getServerProfileByEmail,
  saveServerProfile,
} from "@/lib/server/profile-store";

function billingEndFromNow(months = 1): string {
  const end = new Date();
  end.setMonth(end.getMonth() + months);
  return end.toISOString();
}

async function resolveProfile(
  payload: SubscriptionActivatedPayload
): Promise<UserProfile> {
  let profile: UserProfile | null = null;

  if (payload.email) {
    profile = await getServerProfileByEmail(payload.email);
  }
  if (!profile) {
    profile = await getServerProfile(payload.userId);
  }
  if (profile.id === "local-user" && payload.userId !== "local-user") {
    profile = { ...profile, id: payload.userId };
  }
  if (!profile.email && payload.email) {
    profile = { ...profile, email: payload.email };
  }
  return profile;
}

function applyMonthlyFromWebhook(
  payload: SubscriptionActivatedPayload,
  tier: "standard" | "premium",
  defaultGrant: number
): Promise<UserProfile> {
  return resolveProfile(payload).then((profile) => {
    const now = new Date();
    const remaining =
      profile.subscriptionActive &&
      profile.tier === tier &&
      profile.creditsExpireAt &&
      new Date(profile.creditsExpireAt) > now
        ? profile.credits
        : 0;

    const credits = remaining + (payload.creditsToGrant || defaultGrant);
    const periodEnd = payload.billingPeriodEnd || billingEndFromNow();

    const updated: UserProfile = {
      ...profile,
      tier,
      subscriptionActive: true,
      credits,
      creditsExpireAt: periodEnd,
      subscriptionRenewsAt: periodEnd,
      hasUsedFreeTrial: profile.hasUsedFreeTrial ?? profile.freeTrialUsed ?? false,
      paymentProvider: payload.provider,
      externalCustomerId: payload.externalCustomerId,
      externalSubscriptionId: payload.externalSubscriptionId,
      updatedAt: now.toISOString(),
    };

    return saveServerProfile(updated);
  });
}

/** Apply Standard ($89 / 2000 credits / 1 month) */
export async function applyStandardFromWebhook(
  payload: SubscriptionActivatedPayload
): Promise<UserProfile> {
  return applyMonthlyFromWebhook(payload, "standard", STANDARD_CREDITS);
}

/** Apply Premium cinematic ($249 / 2000 credits / 1 month) */
export async function applyPremiumFromWebhook(
  payload: SubscriptionActivatedPayload
): Promise<UserProfile> {
  return applyMonthlyFromWebhook(payload, "premium", PREMIUM_CREDITS);
}

export async function applyPlanFromWebhook(
  payload: SubscriptionActivatedPayload
): Promise<UserProfile> {
  if (payload.planType === "tester") {
    throw new Error(
      "Tester publishing plans are handled by RTAS Omni Reach AI."
    );
  }
  if (payload.planType === "premium") {
    return applyPremiumFromWebhook(payload);
  }
  return applyStandardFromWebhook(payload);
}

export async function cancelPremiumFromWebhook(
  payload: SubscriptionCancelledPayload
): Promise<UserProfile> {
  const profile = await getServerProfile(payload.userId);
  const updated: UserProfile = {
    ...profile,
    tier: "free",
    subscriptionActive: false,
    subscriptionRenewsAt: null,
    updatedAt: new Date().toISOString(),
  };
  return saveServerProfile(updated);
}
