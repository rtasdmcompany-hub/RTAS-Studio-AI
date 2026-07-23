import { NextResponse } from "next/server";
import { fetchAiUsageAnalytics } from "@/lib/server/admin/executive-bi";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const url = new URL(request.url);
  const days = Number(url.searchParams.get("days") || 30);

  try {
    const analytics = await fetchAiUsageAnalytics(days);
    return NextResponse.json({ ok: true, analytics });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "AI usage analytics unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
