import {
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  type SubscriptionActivatedPayload,
  type UserProfile,
} from "@rtas/shared";
import {
  getServerProfile,
  getServerProfileByEmail,
  saveServerProfile,
} from "@/lib/server/profile-store";
import { upsertTesterSubscriptionFromWebhook } from "@/lib/server/tester-subscription";

function testerEndFromNow(): string {
  const end = new Date();
  end.setDate(end.getDate() + TESTER_DURATION_DAYS);
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

/** Apply Omni Reach Tester ($5 / 5 days / 30s publishing cap) from MoR webhook */
export async function applyTesterFromWebhook(
  payload: SubscriptionActivatedPayload
): Promise<UserProfile> {
  const profile = await resolveProfile(payload);
  const now = new Date();
  const periodEnd = payload.billingPeriodEnd || testerEndFromNow();

  const updated: UserProfile = {
    ...profile,
    tier: "tester",
    subscriptionActive: true,
    credits: payload.creditsToGrant || TESTER_CREDITS,
    creditsExpireAt: periodEnd,
    subscriptionRenewsAt: null,
    hasUsedFreeTrial: true,
    freeTrialUsed: true,
    paymentProvider: payload.provider,
    externalCustomerId: payload.externalCustomerId,
    externalSubscriptionId: payload.externalSubscriptionId,
    updatedAt: now.toISOString(),
  };

  const saved = await saveServerProfile(updated);
  await upsertTesterSubscriptionFromWebhook(saved.id, payload);
  return saved;
}

export async function applyPlanFromWebhook(
  payload: SubscriptionActivatedPayload
): Promise<UserProfile> {
  if (payload.planType !== "tester") {
    throw new Error(
      "Omni Reach webhooks only accept the $5 Tester publishing plan."
    );
  }
  return applyTesterFromWebhook(payload);
}
