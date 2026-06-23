import crypto from "crypto";
import type { PaymentWebhookEvent } from "@rtas/shared";
import {
  billingEndForPlan,
  creditsForPlan,
  resolvePlanFromCustomData,
  resolvePlanFromVariantId,
} from "./plan-detect";

/** Lemon Squeezy webhook envelope */
export interface LemonSqueezyWebhookBody {
  meta?: {
    event_name?: string;
    custom_data?: Record<string, string>;
  };
  data?: {
    id?: string;
    attributes?: {
      customer_id?: number;
      user_email?: string;
      renews_at?: string;
      ends_at?: string;
      status?: string;
      variant_id?: number;
    };
  };
}

export function verifyLemonSqueezySignature(
  rawBody: string,
  signatureHeader: string | null
): boolean {
  const secret = process.env.LEMONSQUEEZY_WEBHOOK_SECRET;
  if (!secret) {
    return process.env.NODE_ENV === "development";
  }
  if (!signatureHeader) return false;

  const digest = crypto.createHmac("sha256", secret).update(rawBody).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(signatureHeader), Buffer.from(digest));
  } catch {
    return false;
  }
}

export function parseLemonSqueezyWebhook(
  body: LemonSqueezyWebhookBody
): PaymentWebhookEvent {
  const eventName = body.meta?.event_name ?? "";
  const custom = body.meta?.custom_data ?? {};
  const attrs = body.data?.attributes;
  const userId = custom.user_id ?? custom.userId ?? "local-user";

  const paidEvents = [
    "subscription_created",
    "subscription_payment_success",
    "order_created",
  ];

  if (paidEvents.includes(eventName) && attrs?.status !== "cancelled") {
    const planType =
      resolvePlanFromVariantId(attrs?.variant_id) ??
      resolvePlanFromCustomData(custom);
    const payload = {
      userId,
      email: attrs?.user_email ?? custom.email,
      externalCustomerId: String(attrs?.customer_id ?? ""),
      externalSubscriptionId: String(body.data?.id ?? ""),
      provider: "lemon_squeezy" as const,
      planType,
      creditsToGrant: creditsForPlan(planType),
      billingPeriodEnd: billingEndForPlan(
        planType,
        attrs?.renews_at ?? attrs?.ends_at
      ),
      paymentId: String(body.data?.id ?? ""),
    };
    return { type: "subscription_activated", provider: "lemon_squeezy", payload };
  }

  if (
    eventName === "subscription_cancelled" ||
    eventName === "subscription_expired"
  ) {
    return {
      type: "subscription_cancelled",
      provider: "lemon_squeezy",
      payload: {
        userId,
        externalSubscriptionId: String(body.data?.id ?? ""),
        provider: "lemon_squeezy",
      },
    };
  }

  return {
    type: "ignored",
    provider: "lemon_squeezy",
    reason: eventName || "unknown_event",
  };
}

export const LEMONSQUEEZY_CHECKOUT_CONFIG = {
  storeId: process.env.LEMONSQUEEZY_STORE_ID ?? "",
  variantId: process.env.LEMONSQUEEZY_VARIANT_ID ?? "",
  successUrl: "/studio?payment=success",
};
