import { NextResponse } from "next/server";
import {
  fetchRevenuePeriodReport,
  type PeriodKey,
} from "@/lib/server/admin/executive-bi";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const PERIODS: PeriodKey[] = [
  "daily",
  "weekly",
  "monthly",
  "quarterly",
  "yearly",
];

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const url = new URL(request.url);
  const periodParam = (url.searchParams.get("period") || "monthly") as PeriodKey;
  const period = PERIODS.includes(periodParam) ? periodParam : "monthly";

  try {
    const report = await fetchRevenuePeriodReport(period);
    return NextResponse.json({ ok: true, report, periods: PERIODS });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Revenue report unavailable";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
