import crypto from "crypto";
import { PREMIUM_PLAN_ID, type PaymentWebhookEvent } from "@rtas/shared";
import {
  billingEndForPlan,
  creditsForPlan,
  resolvePlanFromCustomData,
  resolvePlanFromVariantId,
} from "./plan-detect";

/** Paddle Billing webhook payload (simplified — extend per Paddle docs) */
export interface PaddleWebhookBody {
  event_type?: string;
  data?: {
    id?: string;
    customer_id?: string;
    custom_data?: Record<string, string>;
    current_billing_period?: { ends_at?: string };
    items?: { price?: { id?: string } }[];
  };
}

export function verifyPaddleSignature(
  rawBody: string,
  signatureHeader: string | null
): boolean {
  const secret = process.env.PADDLE_WEBHOOK_SECRET;
  if (!secret) {
    // Dev: allow unsigned when secret not configured
    return process.env.NODE_ENV === "development";
  }
  if (!signatureHeader) return false;

  // Paddle Billing: ts;h1 signature format
  const parts = signatureHeader.split(";");
  const h1 = parts.find((p) => p.startsWith("h1="))?.slice(3);
  if (!h1) return false;

  const ts = parts.find((p) => p.startsWith("ts="))?.slice(3) ?? "";
  const signed = `${ts}:${rawBody}`;
  const expected = crypto.createHmac("sha256", secret).update(signed).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(h1), Buffer.from(expected));
  } catch {
    return false;
  }
}

export function parsePaddleWebhook(body: PaddleWebhookBody): PaymentWebhookEvent {
  const eventType = body.event_type ?? "";
  const data = body.data;
  const custom = data?.custom_data ?? {};
  const userId = custom.user_id ?? custom.userId ?? "local-user";

  const activatedTypes = [
    "subscription.created",
    "subscription.activated",
    "transaction.completed",
  ];

  if (activatedTypes.includes(eventType)) {
    const priceId = data?.items?.[0]?.price?.id;
    const planType =
      resolvePlanFromVariantId(priceId) ?? resolvePlanFromCustomData(custom);
    const payload = {
      userId,
      email: custom.email,
      externalCustomerId: data?.customer_id ?? "",
      externalSubscriptionId: data?.id ?? "",
      provider: "paddle" as const,
      planType,
      creditsToGrant: creditsForPlan(planType),
      billingPeriodEnd: billingEndForPlan(
        planType,
        data?.current_billing_period?.ends_at
      ),
      paymentId: data?.id ?? custom.transaction_id,
    };
    return { type: "subscription_activated", provider: "paddle", payload };
  }

  if (eventType === "subscription.canceled") {
    return {
      type: "subscription_cancelled",
      provider: "paddle",
      payload: {
        userId,
        externalSubscriptionId: data?.id ?? "",
        provider: "paddle",
      },
    };
  }

  return { type: "ignored", provider: "paddle", reason: eventType || "unknown_event" };
}

export const PADDLE_CHECKOUT_CONFIG = {
  planId: PREMIUM_PLAN_ID,
  priceUsd: 89,
  successUrl: "/studio?payment=success",
};
