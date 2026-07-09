import { NextResponse } from "next/server";
import { refreshAdminFundingSnapshot } from "@/lib/admin-api";

export const runtime = "nodejs";

/** Proxy refresh to the web app admin API (checkout/profile use the same endpoint). */
export async function GET() {
  const result = await refreshAdminFundingSnapshot();
  if (!result.ok) {
    return NextResponse.json({ ok: false, error: result.error }, { status: 502 });
  }
  return NextResponse.redirect(new URL("/", process.env.ADMIN_APP_URL ?? "http://localhost:3002"));
}

export async function POST() {
  const result = await refreshAdminFundingSnapshot();
  return NextResponse.json(result, { status: result.ok ? 200 : 502 });
}
