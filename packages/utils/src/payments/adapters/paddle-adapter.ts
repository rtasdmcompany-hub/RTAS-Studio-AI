import type { PaidPlanType, PaymentProvider } from "@rtas/shared";
import type {
  CheckoutCreateInput,
  CheckoutCreateResult,
  PaymentProviderAdapter,
  WebhookHeaders,
} from "../types";
import {
  parsePaddleWebhook,
  verifyPaddleSignature,
  type PaddleWebhookBody,
} from "../paddle";

function paddlePriceIdForPlan(plan: PaidPlanType): string {
  if (plan === "tester") return process.env.PADDLE_TESTER_PRICE_ID?.trim() || "";
  if (plan === "premium")
    return process.env.PADDLE_PREMIUM_PRICE_ID?.trim() || "";
  return (
    process.env.PADDLE_STANDARD_PRICE_ID?.trim() ||
    process.env.PADDLE_PRICE_ID?.trim() ||
    ""
  );
}

function staticPaddleCheckoutUrl(plan: PaidPlanType): string {
  if (plan === "tester")
    return process.env.NEXT_PUBLIC_PADDLE_TESTER_CHECKOUT_URL?.trim() || "";
  if (plan === "premium") {
    return (
      process.env.NEXT_PUBLIC_PADDLE_PREMIUM_CHECKOUT_URL?.trim() ||
      process.env.NEXT_PUBLIC_PADDLE_CHECKOUT_URL?.trim() ||
      ""
    );
  }
  return (
    process.env.NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL?.trim() ||
    process.env.NEXT_PUBLIC_PADDLE_CHECKOUT_URL?.trim() ||
    ""
  );
}

async function createPaddleApiCheckout(
  input: CheckoutCreateInput
): Promise<string | null> {
  const apiKey = process.env.PADDLE_API_KEY?.trim();
  const priceId = paddlePriceIdForPlan(input.plan);
  if (!apiKey || !priceId) return null;

  const res = await fetch("https://api.paddle.com/transactions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      items: [{ price_id: priceId, quantity: 1 }],
      collection_mode: "automatic",
      customer: input.email ? { email: input.email } : undefined,
      custom_data: {
        user_id: input.userId,
        email: input.email,
        plan: input.plan,
        billing_cycle: input.billingCycle ?? "monthly",
      },
    }),
  });

  if (!res.ok) {
    console.error(
      "[paddle-adapter] transaction failed",
      res.status,
      (await res.text()).slice(0, 400)
    );
    return null;
  }

  const json = (await res.json()) as {
    data?: { checkout?: { url?: string | null } };
  };
  return json.data?.checkout?.url?.trim() || null;
}

export const paddleAdapter: PaymentProviderAdapter = {
  id: "paddle" as PaymentProvider,

  isConfigured() {
    return Boolean(
      process.env.PADDLE_API_KEY?.trim() ||
        process.env.NEXT_PUBLIC_PADDLE_CHECKOUT_URL?.trim() ||
        process.env.NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL?.trim() ||
        process.env.PADDLE_STANDARD_PRICE_ID?.trim()
    );
  },

  async createCheckout(input): Promise<CheckoutCreateResult> {
    const liveUrl = await createPaddleApiCheckout(input);
    if (liveUrl) {
      return { ok: true, url: liveUrl, provider: "paddle" };
    }

    const checkoutUrl = staticPaddleCheckoutUrl(input.plan);
    if (checkoutUrl) {
      const url = new URL(checkoutUrl);
      url.searchParams.set(
        "passthrough",
        JSON.stringify({
          user_id: input.userId,
          email: input.email,
          plan: input.plan,
        })
      );
      return { ok: true, url: url.toString(), provider: "paddle" };
    }

    return {
      ok: false,
      provider: "paddle",
      code: "PADDLE_NOT_CONFIGURED",
      error:
        "Paddle checkout is not configured. Set PADDLE_API_KEY + price IDs or static checkout URLs.",
    };
  },

  verifyWebhook(rawBody, headers: WebhookHeaders) {
    const signature =
      headers.get("paddle-signature") ?? headers.get("Paddle-Signature");
    return verifyPaddleSignature(rawBody, signature);
  },

  parseWebhook(body: unknown) {
    return parsePaddleWebhook(body as PaddleWebhookBody);
  },
};
