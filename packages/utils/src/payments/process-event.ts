/**
 * Pure billing state transitions — unit-testable without Next.js / Prisma.
 * Never invents successful payments; only maps verified webhook events → profile deltas.
 */

import {
  TESTER_DURATION_DAYS,
  priceUsdForPaidPlan,
  type PaymentWebhookEvent,
  type SubscriptionActivatedPayload,
  type UserProfile,
} from "@rtas/shared";

export type LedgerAction =
  | {
      kind: "transaction";
      status: "completed" | "failed" | "refunded" | "cancelled";
      eventType: string;
      amountUsd: number;
      creditsGranted: number;
      planKey?: string;
      paymentId?: string;
      externalSubscriptionId?: string;
    }
  | {
      kind: "invoice";
      status: "paid" | "void" | "open";
      amountUsd: number;
      planKey: string;
      periodEnd?: string;
      paymentId?: string;
    }
  | {
      kind: "subscription_upsert";
      planKey: string;
      status: "active" | "cancelled" | "expired" | "past_due";
      billingCycle: string;
      externalSubscriptionId?: string;
      periodEnd?: string;
      cancelAtPeriodEnd?: boolean;
    }
  | { kind: "audit"; detail: string; eventType: string };

export type BillingProcessResult = {
  profile: UserProfile;
  actions: LedgerAction[];
  applied: boolean;
  duplicateSafe: boolean;
};

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

function applyActivation(
  profile: UserProfile,
  payload: SubscriptionActivatedPayload,
  eventType: "subscription_activated" | "subscription_renewed"
): BillingProcessResult {
  if (!payload.userId?.trim()) {
    throw new Error("Webhook missing user_id — refusing to apply subscription.");
  }

  const isTester = payload.planType === "tester";
  const tier = isTester
    ? "tester"
    : payload.planType === "premium"
      ? "premium"
      : "standard";
  const now = new Date();
  const remaining =
    !isTester &&
    profile.subscriptionActive &&
    profile.tier === tier &&
    profile.creditsExpireAt &&
    new Date(profile.creditsExpireAt) > now
      ? profile.credits
      : 0;

  const grant = payload.creditsToGrant || 0;
  const credits = remaining + grant;
  const periodEnd =
    payload.billingPeriodEnd ||
    (isTester ? testerEndFromNow() : billingEndFromNow());
  const amountUsd = payload.amountUsd ?? priceUsdForPaidPlan(payload.planType);
  const billingCycle =
    payload.billingCycle ?? (isTester ? "one_time" : "monthly");

  const updated: UserProfile = {
    ...profile,
    id: profile.id === "local-user" && payload.userId !== "local-user"
      ? payload.userId
      : profile.id,
    email: profile.email || payload.email || "",
    tier,
    subscriptionActive: true,
    credits,
    creditsExpireAt: periodEnd,
    // Tester is a fixed window, not a monthly renewing sub.
    subscriptionRenewsAt: isTester ? null : periodEnd,
    hasUsedFreeTrial: true,
    freeTrialUsed: true,
    paymentProvider: payload.provider,
    externalCustomerId: payload.externalCustomerId,
    externalSubscriptionId: payload.externalSubscriptionId,
    updatedAt: now.toISOString(),
  };

  return {
    profile: updated,
    applied: true,
    duplicateSafe: true,
    actions: [
      {
        kind: "transaction",
        status: "completed",
        eventType,
        amountUsd,
        creditsGranted: grant,
        planKey: payload.planType,
        paymentId: payload.paymentId,
        externalSubscriptionId: payload.externalSubscriptionId,
      },
      {
        kind: "invoice",
        status: "paid",
        amountUsd,
        planKey: payload.planType,
        periodEnd,
        paymentId: payload.paymentId,
      },
      {
        kind: "subscription_upsert",
        planKey: payload.planType,
        status: "active",
        billingCycle,
        externalSubscriptionId: payload.externalSubscriptionId,
        periodEnd,
        cancelAtPeriodEnd: false,
      },
      {
        kind: "audit",
        eventType,
        detail: `${eventType} ${payload.planType} +${grant} credits`,
      },
    ],
  };
}

function applyCancel(
  profile: UserProfile,
  immediate: boolean,
  eventType: string
): BillingProcessResult {
  const now = new Date().toISOString();
  if (!immediate && profile.subscriptionRenewsAt) {
    return {
      profile: {
        ...profile,
        updatedAt: now,
      },
      applied: true,
      duplicateSafe: true,
      actions: [
        {
          kind: "subscription_upsert",
          planKey: profile.tier === "premium" ? "premium" : "standard",
          status: "cancelled",
          billingCycle: "monthly",
          externalSubscriptionId: profile.externalSubscriptionId,
          periodEnd: profile.subscriptionRenewsAt ?? undefined,
          cancelAtPeriodEnd: true,
        },
        {
          kind: "audit",
          eventType,
          detail: "cancel_at_period_end",
        },
      ],
    };
  }

  return {
    profile: {
      ...profile,
      tier: "free",
      subscriptionActive: false,
      subscriptionRenewsAt: null,
      updatedAt: now,
    },
    applied: true,
    duplicateSafe: true,
    actions: [
      {
        kind: "subscription_upsert",
        planKey: "free",
        status: eventType.includes("expired") ? "expired" : "cancelled",
        billingCycle: "monthly",
        externalSubscriptionId: profile.externalSubscriptionId,
        cancelAtPeriodEnd: false,
      },
      {
        kind: "audit",
        eventType,
        detail: immediate ? "access_ended" : "cancelled",
      },
    ],
  };
}

/**
 * Apply a verified, normalized webhook event to a user profile.
 */
export function processPaymentEvent(
  profile: UserProfile,
  event: PaymentWebhookEvent
): BillingProcessResult {
  switch (event.type) {
    case "subscription_activated":
    case "subscription_renewed":
      return applyActivation(profile, event.payload, event.type);

    case "subscription_cancelled":
      return applyCancel(
        profile,
        event.payload.immediate === true,
        event.type
      );

    case "subscription_expired":
      return applyCancel(profile, true, event.type);

    case "payment_failed": {
      const now = new Date().toISOString();
      return {
        profile: {
          ...profile,
          // Keep access until period end; mark past_due in ledger only
          updatedAt: now,
        },
        applied: true,
        duplicateSafe: true,
        actions: [
          {
            kind: "transaction",
            status: "failed",
            eventType: "payment_failed",
            amountUsd: 0,
            creditsGranted: 0,
            paymentId: event.payload.paymentId,
            externalSubscriptionId: event.payload.externalSubscriptionId,
          },
          {
            kind: "subscription_upsert",
            planKey:
              profile.tier === "premium"
                ? "premium"
                : profile.tier === "standard"
                  ? "standard"
                  : "free",
            status: "past_due",
            billingCycle: "monthly",
            externalSubscriptionId:
              event.payload.externalSubscriptionId ??
              profile.externalSubscriptionId,
            periodEnd: profile.subscriptionRenewsAt ?? undefined,
          },
          {
            kind: "audit",
            eventType: "payment_failed",
            detail: event.payload.reason ?? "payment_failed",
          },
        ],
      };
    }

    case "payment_refunded": {
      const revoke = Math.max(0, event.payload.creditsToRevoke ?? 0);
      const credits = Math.max(0, profile.credits - revoke);
      const now = new Date().toISOString();
      return {
        profile: {
          ...profile,
          credits,
          // Full refund of active sub → deactivate
          ...(revoke > 0 && credits === 0
            ? {
                tier: "free" as const,
                subscriptionActive: false,
                subscriptionRenewsAt: null,
              }
            : {}),
          updatedAt: now,
        },
        applied: true,
        duplicateSafe: true,
        actions: [
          {
            kind: "transaction",
            status: "refunded",
            eventType: "payment_refunded",
            amountUsd: event.payload.amountUsd ?? 0,
            creditsGranted: -revoke,
            paymentId: event.payload.paymentId,
            externalSubscriptionId: event.payload.externalSubscriptionId,
          },
          {
            kind: "invoice",
            status: "void",
            amountUsd: event.payload.amountUsd ?? 0,
            planKey: profile.tier,
            paymentId: event.payload.paymentId,
          },
          {
            kind: "audit",
            eventType: "payment_refunded",
            detail: `revoked ${revoke} credits`,
          },
        ],
      };
    }

    case "checkout_cancelled":
      return {
        profile,
        applied: false,
        duplicateSafe: true,
        actions: [
          {
            kind: "transaction",
            status: "cancelled",
            eventType: "checkout_cancelled",
            amountUsd: 0,
            creditsGranted: 0,
            paymentId: event.payload.paymentId,
          },
          {
            kind: "audit",
            eventType: "checkout_cancelled",
            detail: event.payload.reason ?? "checkout_cancelled",
          },
        ],
      };

    case "ignored":
    default:
      return {
        profile,
        applied: false,
        duplicateSafe: true,
        actions: [
          {
            kind: "audit",
            eventType: "ignored",
            detail: event.type === "ignored" ? event.reason : event.type,
          },
        ],
      };
  }
}
