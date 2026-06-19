import { NextResponse } from "next/server";
import { evaluateFalPoolHealth } from "@/lib/payments/fal-funding-service";

export const runtime = "nodejs";

/** Re-check Fal pool after demo/local payment activation */
export async function POST() {
  const snapshot = await evaluateFalPoolHealth();
  return NextResponse.json({ ok: true, snapshot });
}
