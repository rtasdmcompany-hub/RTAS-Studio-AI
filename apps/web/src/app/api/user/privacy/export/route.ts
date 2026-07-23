import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import { buildPersonalDataExport } from "@/lib/server/privacy-data";
import { logEvent } from "@/lib/observability";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * Download a JSON export of the signed-in user's personal data.
 * GET /api/user/privacy/export
 */
export async function GET() {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const limited = await checkRateLimitAsync(
    `privacy-export:${auth.userId}`,
    5,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  try {
    const payload = await buildPersonalDataExport(auth.userId);
    logEvent("info", "privacy.export", { userId: auth.userId });
    const body = JSON.stringify(payload, null, 2);
    return new NextResponse(body, {
      status: 200,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Disposition": `attachment; filename="rtas-personal-data-${auth.userId.slice(0, 8)}.json"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (err) {
    logEvent("error", "privacy.export.failed", {
      userId: auth.userId,
      message: err instanceof Error ? err.message : "unknown",
    });
    return NextResponse.json(
      { error: "Could not build personal data export. Try again or email privacy@rtasstudio.com." },
      { status: 500 }
    );
  }
}
