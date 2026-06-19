import { NextResponse } from "next/server";
import {
  evaluateFalPoolHealth,
} from "@/lib/payments/fal-funding-service";
import { getFalLedgerSummary } from "@/lib/server/fal-ledger-store";

export const runtime = "nodejs";

function isAuthorized(request: Request): boolean {
  const secret = process.env.RTAS_ADMIN_SECRET?.trim();
  if (!secret) return process.env.NODE_ENV === "development";
  const header = request.headers.get("x-rtas-admin-secret");
  return header === secret;
}

/** Owner: Fal pool status + ledger (protect with RTAS_ADMIN_SECRET in production) */
export async function GET(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const snapshot = await evaluateFalPoolHealth();
  const ledger = await getFalLedgerSummary();

  return NextResponse.json({
    snapshot,
    ledger,
    falBillingUrl: "https://fal.ai/dashboard/billing",
    autoRechargeHint:
      "Enable auto-recharge on Fal billing — RTAS monitors balance vs active customers after each payment.",
  });
}
