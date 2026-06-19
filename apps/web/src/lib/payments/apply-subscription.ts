import {

  PREMIUM_CREDITS,

  STANDARD_CREDITS,

  TESTER_CREDITS,

  TESTER_DURATION_DAYS,

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



/** Apply Tester ($5 / 30 credits / 5 days) from MoR webhook */

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



  return saveServerProfile(updated);

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

    return applyTesterFromWebhook(payload);

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


