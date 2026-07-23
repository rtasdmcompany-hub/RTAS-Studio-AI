import { NextResponse } from "next/server";
import { fetchRevenueOpsMetrics } from "@/lib/server/admin/revenue-metrics";
import { isAdminAuthorized, adminUnauthorizedResponse } from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  try {
    const metrics = await fetchRevenueOpsMetrics();
    return NextResponse.json({ ok: true, metrics });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Revenue ops unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
