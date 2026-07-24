import type {
  BillingCycle,
  PaidPlanType,
  PaymentProvider,
  PaymentWebhookEvent,
} from "@rtas/shared";

export type CheckoutCreateInput = {
  userId: string;
  email: string;
  plan: PaidPlanType;
  billingCycle?: BillingCycle;
  successUrl?: string;
};

export type CheckoutCreateResult =
  | { ok: true; url: string; provider: PaymentProvider }
  | { ok: false; error: string; provider: PaymentProvider; code?: string };

export type WebhookHeaders = {
  get(name: string): string | null;
};

/**
 * Provider-independent payment adapter.
 * Implementations must verify signatures and never report success without provider proof.
 */
export interface PaymentProviderAdapter {
  readonly id: PaymentProvider;
  isConfigured(): boolean;
  createCheckout(input: CheckoutCreateInput): Promise<CheckoutCreateResult>;
  verifyWebhook(rawBody: string, headers: WebhookHeaders): boolean;
  parseWebhook(body: unknown): PaymentWebhookEvent;
}
