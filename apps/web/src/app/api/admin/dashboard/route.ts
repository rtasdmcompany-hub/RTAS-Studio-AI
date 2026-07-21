import { NextResponse } from "next/server";
import { fetchAdminDashboardMetrics } from "@/lib/server/admin/metrics";
import { isAdminAuthorized, adminUnauthorizedResponse } from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  try {
    const metrics = await fetchAdminDashboardMetrics();
    return NextResponse.json({ ok: true, metrics });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Dashboard unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
