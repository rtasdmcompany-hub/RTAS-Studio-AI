import { NextResponse } from "next/server";
import { evaluateFalPoolHealth } from "@/lib/payments/fal-funding-service";
import {
  adminUnauthorizedResponse,
  isAdminAuthorized,
} from "@/lib/server/api-auth";

export const runtime = "nodejs";

/** Re-check Fal pool after demo/local payment activation */
export async function POST(request: Request) {
  if (!isAdminAuthorized(request)) {
    return adminUnauthorizedResponse();
  }

  const snapshot = await evaluateFalPoolHealth();
  return NextResponse.json({ ok: true, snapshot });
}
