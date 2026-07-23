import { NextResponse } from "next/server";
import { fetchExecutiveKpis } from "@/lib/server/admin/executive-bi";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  try {
    const kpis = await fetchExecutiveKpis();
    return NextResponse.json({ ok: true, kpis });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Executive KPIs unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
