import { NextResponse } from "next/server";
import { getObservabilityStatus } from "@/lib/observability";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * Liveness probe — process is up. No dependency checks.
 * Use for uptime monitors and load balancers.
 * GET /api/health
 */
export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "rtas-web",
      timestamp: new Date().toISOString(),
      observability: getObservabilityStatus(),
    },
    {
      status: 200,
      headers: {
        "Cache-Control": "no-store, max-age=0",
      },
    }
  );
}
