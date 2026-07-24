import {
  RECOMMENDED_PAYMENT_PROVIDER,
  type PaymentProvider,
} from "@rtas/shared";
import { lemonSqueezyAdapter } from "./adapters/lemon-squeezy-adapter";
import { paddleAdapter } from "./adapters/paddle-adapter";
import type {
  CheckoutCreateInput,
  CheckoutCreateResult,
  PaymentProviderAdapter,
} from "./types";

const ADAPTERS: Record<
  Exclude<PaymentProvider, "manual">,
  PaymentProviderAdapter
> = {
  lemon_squeezy: lemonSqueezyAdapter,
  paddle: paddleAdapter,
};

/** Active MoR from ENV — does not invent a provider. */
export function resolveActivePaymentProvider(): PaymentProvider | null {
  const raw = (process.env.NEXT_PUBLIC_PAYMENT_PROVIDER || "").trim();
  if (raw === "paddle") return "paddle";
  if (raw === "lemon_squeezy") return "lemon_squeezy";
  return null;
}

export function getPaymentAdapter(
  provider?: PaymentProvider | null
): PaymentProviderAdapter | null {
  const id = provider ?? resolveActivePaymentProvider();
  if (!id || id === "manual") return null;
  return ADAPTERS[id] ?? null;
}

export function getRecommendedPaymentAdapter(): PaymentProviderAdapter {
  return ADAPTERS[RECOMMENDED_PAYMENT_PROVIDER];
}

export async function createProviderCheckout(
  input: CheckoutCreateInput,
  provider?: PaymentProvider | null
): Promise<CheckoutCreateResult> {
  const adapter = getPaymentAdapter(provider);
  if (!adapter) {
    return {
      ok: false,
      provider: "manual",
      code: "NO_PROVIDER",
      error:
        "No payment provider configured. Set NEXT_PUBLIC_PAYMENT_PROVIDER to lemon_squeezy or paddle.",
    };
  }
  return adapter.createCheckout(input);
}

export { ADAPTERS };
