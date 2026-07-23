import { NextResponse } from "next/server";
import { evaluateBusinessAlerts } from "@/lib/server/admin/business-alerts";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const url = new URL(request.url);
  const persist = url.searchParams.get("persist") !== "0";

  try {
    const result = await evaluateBusinessAlerts({ persist });
    return NextResponse.json({ ok: true, ...result });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Business alerts unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
