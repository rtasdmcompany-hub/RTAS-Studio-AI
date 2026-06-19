import { NextResponse } from "next/server";
import { MONTHLY_CREDITS, MONTHLY_PRICE_USD, PREMIUM_PLAN_ID } from "@rtas/shared";
import { PADDLE_CHECKOUT_CONFIG } from "@/lib/payments/paddle";
import { LEMONSQUEEZY_CHECKOUT_CONFIG } from "@/lib/payments/lemon-squeezy";
import { getActivePaymentProvider } from "@/lib/monetization";

export async function GET() {
  const provider = getActivePaymentProvider();

  return NextResponse.json({
    provider,
    premium: {
      priceUsd: MONTHLY_PRICE_USD,
      credits: MONTHLY_CREDITS,
      planId: PREMIUM_PLAN_ID,
    },
    paddle:
      provider === "paddle"
        ? {
            ...PADDLE_CHECKOUT_CONFIG,
            clientToken: process.env.NEXT_PUBLIC_PADDLE_CLIENT_TOKEN ?? null,
          }
        : null,
    lemonSqueezy:
      provider === "lemon_squeezy"
        ? {
            ...LEMONSQUEEZY_CHECKOUT_CONFIG,
            checkoutUrl: process.env.NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL ?? null,
          }
        : null,
    webhooks: {
      paddle: "/api/webhooks/paddle",
      lemonSqueezy: "/api/webhooks/lemon-squeezy",
    },
  });
}
