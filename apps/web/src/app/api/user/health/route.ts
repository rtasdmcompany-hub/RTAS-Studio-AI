import { NextResponse } from "next/server";
import { requireApiSession } from "@/lib/server/api-auth";
import { getCustomerHealth } from "@/lib/customer-success/customer-health";
import { isPrismaConfigured } from "@/lib/prisma";

export const runtime = "nodejs";

/** Signed-in user's health snapshot — real data only. */
export async function GET() {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;
  if (!isPrismaConfigured()) {
    return NextResponse.json({ error: "Database is not configured." }, { status: 503 });
  }

  const health = await getCustomerHealth(auth.userId);
  if (!health) {
    return NextResponse.json({ error: "User not found." }, { status: 404 });
  }
  return NextResponse.json({ ok: true, health });
}
