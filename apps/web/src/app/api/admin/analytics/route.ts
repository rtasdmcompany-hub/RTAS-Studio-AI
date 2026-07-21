import { NextResponse } from "next/server";
import { fetchAnalyticsSeries } from "@/lib/server/admin/metrics";
import { isAdminAuthorized, adminUnauthorizedResponse } from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const days = Number(new URL(request.url).searchParams.get("days") ?? "30");
  const windowDays = Number.isFinite(days) ? Math.min(Math.max(days, 7), 90) : 30;

  try {
    const analytics = await fetchAnalyticsSeries(windowDays);
    return NextResponse.json({ ok: true, analytics, days: windowDays });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Analytics unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
