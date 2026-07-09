import { NextResponse } from "next/server";
import { resetBackendFalGuard } from "@/lib/admin-api";

export const runtime = "nodejs";

/** Reset Fal billing guard on the FastAPI backend. */
export async function POST() {
  const result = await resetBackendFalGuard();
  return NextResponse.json(result, { status: result.ok ? 200 : 502 });
}
