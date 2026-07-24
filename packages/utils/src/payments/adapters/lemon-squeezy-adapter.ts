import type { PaidPlanType, PaymentProvider } from "@rtas/shared";
import type {
  CheckoutCreateInput,
  CheckoutCreateResult,
  PaymentProviderAdapter,
  WebhookHeaders,
} from "../types";
import {
  parseLemonSqueezyWebhook,
  verifyLemonSqueezySignature,
  type LemonSqueezyWebhookBody,
} from "../lemon-squeezy";

function lemonVariantIdForPlan(plan: PaidPlanType): string {
  if (plan === "tester")
    return process.env.LEMONSQUEEZY_TESTER_VARIANT_ID?.trim() || "";
  if (plan === "premium")
    return process.env.LEMONSQUEEZY_PREMIUM_VARIANT_ID?.trim() || "";
  return (
    process.env.LEMONSQUEEZY_STANDARD_VARIANT_ID?.trim() ||
    process.env.LEMONSQUEEZY_VARIANT_ID?.trim() ||
    ""
  );
}

function staticLemonCheckoutUrl(plan: PaidPlanType): string {
  if (plan === "tester")
    return process.env.NEXT_PUBLIC_LEMONSQUEEZY_TESTER_CHECKOUT_URL?.trim() || "";
  if (plan === "premium") {
    return (
      process.env.NEXT_PUBLIC_LEMONSQUEEZY_PREMIUM_CHECKOUT_URL?.trim() ||
      process.env.NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL?.trim() ||
      ""
    );
  }
  return (
    process.env.NEXT_PUBLIC_LEMONSQUEEZY_STANDARD_CHECKOUT_URL?.trim() ||
    process.env.NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL?.trim() ||
    ""
  );
}

async function createLemonApiCheckout(
  input: CheckoutCreateInput
): Promise<string | null> {
  const apiKey = process.env.LEMONSQUEEZY_API_KEY?.trim();
  const storeId = process.env.LEMONSQUEEZY_STORE_ID?.trim();
  const variantId = lemonVariantIdForPlan(input.plan);
  if (!apiKey || !storeId || !variantId) return null;

  const res = await fetch("https://api.lemonsqueezy.com/v1/checkouts", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      Accept: "application/vnd.api+json",
      "Content-Type": "application/vnd.api+json",
    },
    body: JSON.stringify({
      data: {
        type: "checkouts",
        attributes: {
          checkout_data: {
            email: input.email || undefined,
            custom: {
              user_id: input.userId,
              plan: input.plan,
              billing_cycle: input.billingCycle ?? "monthly",
            },
          },
          product_options: input.successUrl
            ? { redirect_url: input.successUrl }
            : undefined,
        },
        relationships: {
          store: { data: { type: "stores", id: storeId } },
          variant: { data: { type: "variants", id: variantId } },
        },
      },
    }),
  });

  if (!res.ok) {
    console.error(
      "[lemon-adapter] checkout failed",
      res.status,
      (await res.text()).slice(0, 400)
    );
    return null;
  }

  const json = (await res.json()) as {
    data?: { attributes?: { url?: string } };
  };
  return json.data?.attributes?.url?.trim() || null;
}

export const lemonSqueezyAdapter: PaymentProviderAdapter = {
  id: "lemon_squeezy" as PaymentProvider,

  isConfigured() {
    return Boolean(
      process.env.LEMONSQUEEZY_API_KEY?.trim() ||
        process.env.NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL?.trim() ||
        process.env.NEXT_PUBLIC_LEMONSQUEEZY_STANDARD_CHECKOUT_URL?.trim() ||
        process.env.LEMONSQUEEZY_VARIANT_ID?.trim() ||
        process.env.LEMONSQUEEZY_STANDARD_VARIANT_ID?.trim()
    );
  },

  async createCheckout(input): Promise<CheckoutCreateResult> {
    const liveUrl = await createLemonApiCheckout(input);
    if (liveUrl) {
      return { ok: true, url: liveUrl, provider: "lemon_squeezy" };
    }

    const checkoutUrl = staticLemonCheckoutUrl(input.plan);
    if (checkoutUrl) {
      const sep = checkoutUrl.includes("?") ? "&" : "?";
      const url = `${checkoutUrl}${sep}checkout[custom][user_id]=${encodeURIComponent(input.userId)}&checkout[custom][plan]=${encodeURIComponent(input.plan)}&checkout[email]=${encodeURIComponent(input.email)}`;
      return { ok: true, url, provider: "lemon_squeezy" };
    }

    return {
      ok: false,
      provider: "lemon_squeezy",
      code: "LEMON_NOT_CONFIGURED",
      error:
        "Lemon Squeezy checkout is not configured. Set LEMONSQUEEZY_API_KEY + store/variant IDs or static checkout URLs.",
    };
  },

  verifyWebhook(rawBody, headers: WebhookHeaders) {
    return verifyLemonSqueezySignature(rawBody, headers.get("x-signature"));
  },

  parseWebhook(body: unknown) {
    return parseLemonSqueezyWebhook(body as LemonSqueezyWebhookBody);
  },
};
