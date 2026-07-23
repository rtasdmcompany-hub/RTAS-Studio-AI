import { NextResponse } from "next/server";
import { adminUnauthorizedResponse, isAdminAuthorized } from "@/lib/server/api-auth";
import { listPromotionAdminRows, savePromotionFromAdmin } from "@/lib/promotions/engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function buildSummary(promotions: Awaited<ReturnType<typeof listPromotionAdminRows>>) {
  return promotions.reduce(
    (acc, promotion) => {
      if (promotion.status === "active") acc.active += 1;
      acc.views += promotion.metrics.views;
      acc.clicks += promotion.metrics.clicks;
      acc.conversions += promotion.metrics.conversions;
      acc.revenueGeneratedUsd += promotion.metrics.revenueGeneratedUsd;
      return acc;
    },
    { active: 0, views: 0, clicks: 0, conversions: 0, revenueGeneratedUsd: 0 }
  );
}

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();
  try {
    const promotions = await listPromotionAdminRows();
    return NextResponse.json({
      ok: true,
      promotions,
      summary: buildSummary(promotions),
    });
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "Promotions unavailable." },
      { status: 503 }
    );
  }
}

export async function POST(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();
  const text = await request.text();
  const params = new URLSearchParams(text);
  try {
    await savePromotionFromAdmin(Object.fromEntries(params.entries()));
    const promotions = await listPromotionAdminRows();
    return NextResponse.json({
      ok: true,
      promotions,
      summary: buildSummary(promotions),
    });
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "Could not save promotion." },
      { status: 400 }
    );
  }
}
