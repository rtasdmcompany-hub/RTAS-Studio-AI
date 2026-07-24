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

/** Billing cycle — yearly prices are Planned until shared constants exist */
export type BillingCycle = "monthly" | "yearly" | "one_time";

/** Normalized event after provider-specific parsing */
export type PaymentWebhookEvent =
  | { type: "subscription_activated"; provider: PaymentProvider; payload: SubscriptionActivatedPayload }
  | { type: "subscription_renewed"; provider: PaymentProvider; payload: SubscriptionActivatedPayload }
  | { type: "subscription_cancelled"; provider: PaymentProvider; payload: SubscriptionCancelledPayload }
  | { type: "subscription_expired"; provider: PaymentProvider; payload: SubscriptionCancelledPayload }
  | { type: "payment_failed"; provider: PaymentProvider; payload: PaymentFailedPayload }
  | { type: "payment_refunded"; provider: PaymentProvider; payload: PaymentRefundedPayload }
  | { type: "checkout_cancelled"; provider: PaymentProvider; payload: CheckoutCancelledPayload }
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
  billingCycle?: BillingCycle;
  amountUsd?: number;
  /** Idempotency key (subscription id, order id, or transaction id) */
  paymentId?: string;
}

export interface SubscriptionCancelledPayload {
  userId: string;
  externalSubscriptionId: string;
  provider: PaymentProvider;
  /** When true, access ends immediately; otherwise cancel-at-period-end */
  immediate?: boolean;
}

export interface PaymentFailedPayload {
  userId: string;
  externalSubscriptionId?: string;
  provider: PaymentProvider;
  paymentId?: string;
  reason?: string;
}

export interface PaymentRefundedPayload {
  userId: string;
  externalSubscriptionId?: string;
  provider: PaymentProvider;
  paymentId?: string;
  amountUsd?: number;
  /** Credits to claw back when known */
  creditsToRevoke?: number;
}

export interface CheckoutCancelledPayload {
  userId?: string;
  provider: PaymentProvider;
  paymentId?: string;
  reason?: string;
}

/** Recommended strategic MoR (Sprint 2). Active runtime still follows ENV. */
export const RECOMMENDED_PAYMENT_PROVIDER: PaymentProvider = "lemon_squeezy";

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
