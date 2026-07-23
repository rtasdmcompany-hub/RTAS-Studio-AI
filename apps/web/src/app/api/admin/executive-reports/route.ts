import {
  buildExecutiveReport,
  EXECUTIVE_REPORT_TYPES,
  type ExecutiveReportType,
} from "@/lib/server/admin/executive-reports";
import type { PeriodKey } from "@/lib/server/admin/executive-bi";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";
import { NextResponse } from "next/server";

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
  const type = (url.searchParams.get("type") ||
    "executive_summary") as ExecutiveReportType;
  const format = url.searchParams.get("format") === "html" ? "html" : "csv";
  const periodParam = (url.searchParams.get("period") || "monthly") as PeriodKey;
  const period = PERIODS.includes(periodParam) ? periodParam : "monthly";

  if (!EXECUTIVE_REPORT_TYPES.includes(type)) {
    return NextResponse.json(
      {
        error: "Invalid report type.",
        allowed: EXECUTIVE_REPORT_TYPES,
      },
      { status: 400 }
    );
  }

  try {
    const report = await buildExecutiveReport({ type, format, period });
    return new NextResponse(report.body, {
      status: 200,
      headers: {
        "Content-Type": report.contentType,
        "Content-Disposition": `attachment; filename="${report.filename}"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Report generation failed";
    return NextResponse.json({ ok: false, error: message }, { status: 503 });
  }
}
