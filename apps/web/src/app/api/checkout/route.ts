import { NextResponse } from "next/server";
import type { PaidPlanType } from "@rtas/shared";
import { getActivePaymentProvider } from "@/lib/monetization";

function normalizePlan(raw: unknown): PaidPlanType {
  if (raw === "tester" || raw === "standard" || raw === "premium") return raw;
  return "standard";
}

/**
 * Returns checkout URL for configured Merchant of Record (Paddle / Lemon Squeezy)
 * or demo activation for local development.
 */
export async function POST(request: Request) {
  const provider = getActivePaymentProvider();

  let body: { userId?: string; email?: string; plan?: PaidPlanType } = {};
  try {
    body = await request.json();
  } catch {
    /* optional body */
  }

  const userId = body.userId ?? "local-user";
  const email = body.email ?? "";
  const plan = normalizePlan(body.plan);

  if (provider === "paddle") {
    const checkoutUrl =
      plan === "tester"
        ? process.env.NEXT_PUBLIC_PADDLE_TESTER_CHECKOUT_URL
        : plan === "premium"
          ? process.env.NEXT_PUBLIC_PADDLE_PREMIUM_CHECKOUT_URL ??
            process.env.NEXT_PUBLIC_PADDLE_CHECKOUT_URL
          : process.env.NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL ??
            process.env.NEXT_PUBLIC_PADDLE_CHECKOUT_URL;
    if (checkoutUrl) {
      const url = new URL(checkoutUrl);
      url.searchParams.set(
        "passthrough",
        JSON.stringify({ user_id: userId, email, plan })
      );
      return NextResponse.json({ url: url.toString(), provider: "paddle", plan });
    }
  }

  if (provider === "lemon_squeezy") {
    const checkoutUrl =
      plan === "tester"
        ? process.env.NEXT_PUBLIC_LEMONSQUEEZY_TESTER_CHECKOUT_URL
        : plan === "premium"
          ? process.env.NEXT_PUBLIC_LEMONSQUEEZY_PREMIUM_CHECKOUT_URL ??
            process.env.NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL
          : process.env.NEXT_PUBLIC_LEMONSQUEEZY_STANDARD_CHECKOUT_URL ??
            process.env.NEXT_PUBLIC_LEMONSQUEEZY_CHECKOUT_URL;
    if (checkoutUrl) {
      const sep = checkoutUrl.includes("?") ? "&" : "?";
      return NextResponse.json({
        url: `${checkoutUrl}${sep}checkout[custom][user_id]=${encodeURIComponent(userId)}&checkout[custom][plan]=${encodeURIComponent(plan)}&checkout[email]=${encodeURIComponent(email)}`,
        provider: "lemon_squeezy",
        plan,
      });
    }
  }

  return NextResponse.json({
    demo: true,
    message:
      "Live payment is not configured yet — your plan was activated for development. Add Paddle checkout URLs in .env for production.",
    provider: provider ?? "none",
    plan,
  });
}
