import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "@/lib/auth/auth-options";
import { resolvePromotionsForPlacement } from "@/lib/promotions/engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const placement = url.searchParams.get("placement")?.trim() || "";
  const pagePath = url.searchParams.get("pagePath")?.trim() || "/";
  if (!placement) {
    return NextResponse.json({ ok: false, error: "placement is required" }, { status: 400 });
  }

  const session = await getServerSession(authOptions);
  const country =
    request.headers.get("x-vercel-ip-country") ||
    request.headers.get("x-country-code") ||
    "global";
  const language = request.headers.get("accept-language")?.split(",")[0] || "en";
  const sessionId =
    request.headers.get("x-promo-session-id") ||
    request.headers.get("x-request-id") ||
    undefined;

  const result = await resolvePromotionsForPlacement({
    placement,
    pagePath,
    userId: session?.user?.id,
    sessionId,
    country,
    language,
  });

  return NextResponse.json({
    ok: true,
    sessionId: result.context.sessionId,
    promotions: result.promotions,
  });
}
