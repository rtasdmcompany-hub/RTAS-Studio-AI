import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "./credits";
import type { PaidPlanType } from "./fal-funding";

export const TESTER_PLAN_ID = "rtas-studio-tester-5d";
export const STANDARD_PLAN_ID = "rtas-studio-standard-monthly";
export const PREMIUM_PLAN_ID = "rtas-studio-premium-cinematic-monthly";

export const TESTER_PLAN_PRICE_USD = TESTER_PRICE_USD;
export const TESTER_PLAN_CREDITS = TESTER_CREDITS;
export const TESTER_PLAN_DAYS = TESTER_DURATION_DAYS;

export const STANDARD_PLAN_PRICE_USD = STANDARD_PRICE_USD;
export const STANDARD_MONTHLY_CREDITS = STANDARD_CREDITS;

export const PREMIUM_PLAN_PRICE_USD = PREMIUM_PRICE_USD;
export const PREMIUM_MONTHLY_CREDITS = PREMIUM_CREDITS;

/** @deprecated Use STANDARD_PLAN_PRICE_USD */
export const PREMIUM_PRICE_USD_LEGACY = STANDARD_PRICE_USD;

export type { PaidPlanType };

export type PaymentProvider = "paddle" | "lemon_squeezy" | "manual";

/** Normalized event after provider-specific parsing */
export type PaymentWebhookEvent =
  | { type: "subscription_activated"; provider: PaymentProvider; payload: SubscriptionActivatedPayload }
  | { type: "subscription_renewed"; provider: PaymentProvider; payload: SubscriptionActivatedPayload }
  | { type: "subscription_cancelled"; provider: PaymentProvider; payload: SubscriptionCancelledPayload }
  | { type: "ignored"; provider: PaymentProvider; reason: string };

export interface SubscriptionActivatedPayload {
  userId: string;
  email?: string;
  externalCustomerId: string;
  externalSubscriptionId: string;
  provider: PaymentProvider;
  planType: PaidPlanType;
  creditsToGrant: number;
  billingPeriodEnd: string;
  /** Idempotency key (subscription id, order id, or transaction id) */
  paymentId?: string;
}

export interface SubscriptionCancelledPayload {
  userId: string;
  externalSubscriptionId: string;
  provider: PaymentProvider;
}

export function creditsForPaidPlan(plan: PaidPlanType): number {
  if (plan === "tester") return TESTER_PLAN_CREDITS;
  if (plan === "standard") return STANDARD_MONTHLY_CREDITS;
  return PREMIUM_MONTHLY_CREDITS;
}

export function priceUsdForPaidPlan(plan: PaidPlanType): number {
  if (plan === "tester") return TESTER_PLAN_PRICE_USD;
  if (plan === "standard") return STANDARD_PLAN_PRICE_USD;
  return PREMIUM_PLAN_PRICE_USD;
}
