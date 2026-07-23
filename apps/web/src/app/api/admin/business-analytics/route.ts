import { NextResponse } from "next/server";
import { fetchBusinessAnalyticsCenter } from "@/lib/server/admin/executive-bi";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  try {
    const analytics = await fetchBusinessAnalyticsCenter();
    return NextResponse.json({ ok: true, analytics });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Business analytics unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
