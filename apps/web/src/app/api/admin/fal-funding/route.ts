import { NextResponse } from "next/server";
import {
  evaluateFalPoolHealth,
} from "@/lib/payments/fal-funding-service";
import { getFalLedgerSummary } from "@/lib/server/fal-ledger-store";
import {
  adminUnauthorizedResponse,
  isAdminAuthorized,
} from "@/lib/server/api-auth";

export const runtime = "nodejs";

/** Owner: Fal pool status + ledger (protect with RTAS_ADMIN_SECRET in production) */
export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) {
    return adminUnauthorizedResponse();
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
