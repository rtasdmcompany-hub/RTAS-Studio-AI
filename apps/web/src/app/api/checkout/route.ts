import { NextResponse } from "next/server";
import type { PaidPlanType } from "@rtas/shared";
import { createProviderCheckout } from "@rtas/utils/payments";
import { getActivePaymentProvider } from "@/lib/monetization";
import { requireApiSession } from "@/lib/server/api-auth";

function normalizePlan(raw: unknown): PaidPlanType {
  if (raw === "tester" || raw === "standard" || raw === "premium") return raw;
  return "standard";
}

/**
 * Returns checkout URL for configured Merchant of Record (Lemon Squeezy / Paddle)
 * or demo activation for local development only.
 * Never activates paid plans in production without a live provider checkout URL.
 */
export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const provider = getActivePaymentProvider();

  let body: {
    email?: string;
    plan?: PaidPlanType;
    billingCycle?: string;
    promotionAttribution?: {
      promotionId?: string;
      variantId?: string | null;
      placement?: string;
      pagePath?: string;
      revenueValueUsd?: number;
    };
  } = {};
  try {
    body = await request.json();
  } catch {
    /* optional body */
  }

  const userId = auth.userId;
  const email =
    body.email?.trim() || auth.session.user?.email?.trim() || "";
  const plan = normalizePlan(body.plan);
  const promo = body.promotionAttribution;
  // Yearly prices are Planned — accept the flag for schema/hooks but charge monthly SKUs only.
  const billingCycle =
    body.billingCycle === "yearly" ? ("yearly" as const) : ("monthly" as const);

  if (provider) {
    const result = await createProviderCheckout(
      {
        userId,
        email,
        plan,
        billingCycle: billingCycle === "yearly" ? "monthly" : billingCycle,
        successUrl: (() => {
          const base = `${process.env.NEXTAUTH_URL || "https://rtasstudio.com"}/studio?payment=success`;
          if (!promo?.promotionId || !promo.placement) return base;
          const url = new URL(base);
          url.searchParams.set("promo", promo.promotionId);
          if (promo.variantId) url.searchParams.set("promoVariant", promo.variantId);
          url.searchParams.set("promoPlacement", promo.placement);
          if (promo.pagePath) url.searchParams.set("promoPage", promo.pagePath);
          if (typeof promo.revenueValueUsd === "number") {
            url.searchParams.set("promoRevenueUsd", String(promo.revenueValueUsd));
          }
          return url.toString();
        })(),
      },
      provider
    );

    if (result.ok) {
      return NextResponse.json({
        url: result.url,
        provider: result.provider,
        plan,
        billingCycle,
      });
    }

    // Provider selected but not configured — fail closed in production below.
    if (process.env.NODE_ENV === "production") {
      return NextResponse.json(
        {
          error: result.error,
          code: result.code,
          provider: result.provider,
          plan,
        },
        { status: 503 }
      );
    }
  }

  // Demo checkout is development-only — never activate plans without payment in production.
  if (process.env.NODE_ENV === "production") {
    return NextResponse.json(
      {
        error:
          "Live payment is not configured. Set NEXT_PUBLIC_PAYMENT_PROVIDER and provider checkout credentials before accepting payments.",
        provider: provider ?? "none",
        plan,
      },
      { status: 503 }
    );
  }

  return NextResponse.json({
    demo: true,
    message:
      "Live payment is not configured yet — your plan was activated for development. Add Lemon Squeezy or Paddle checkout credentials in .env for production.",
    provider: provider ?? "none",
    plan,
  });
}
