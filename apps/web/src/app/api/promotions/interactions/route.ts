import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "@/lib/auth/auth-options";
import { recordPromotionInteraction } from "@/lib/promotions/engine";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: {
    promotionId?: string;
    variantId?: string | null;
    action?: "view" | "click" | "dismiss" | "conversion";
    placement?: string;
    pagePath?: string;
    sessionId?: string;
    revenueAmountUsd?: number;
  } = {};

  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON body." }, { status: 400 });
  }

  if (!body.promotionId || !body.action || !body.placement) {
    return NextResponse.json(
      { ok: false, error: "promotionId, action, and placement are required." },
      { status: 400 }
    );
  }

  const session = await getServerSession(authOptions);
  const country =
    request.headers.get("x-vercel-ip-country") ||
    request.headers.get("x-country-code") ||
    "global";
  const language = request.headers.get("accept-language")?.split(",")[0] || "en";

  await recordPromotionInteraction({
    promotionId: body.promotionId,
    variantId: body.variantId,
    action: body.action,
    placement: body.placement,
    pagePath: body.pagePath || "/",
    sessionId: body.sessionId,
    userId: session?.user?.id,
    country,
    language,
    revenueAmountCents: Math.round((body.revenueAmountUsd ?? 0) * 100),
  });

  return NextResponse.json({ ok: true });
}
