import { NextResponse } from "next/server";
import { requireApiSession } from "@/lib/server/api-auth";
import { getRetentionBundle } from "@/lib/customer-success/retention";
import { isPrismaConfigured } from "@/lib/prisma";

export const runtime = "nodejs";

export async function GET() {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;
  if (!isPrismaConfigured()) {
    return NextResponse.json({ error: "Database is not configured." }, { status: 503 });
  }

  const bundle = await getRetentionBundle(auth.userId);
  if (!bundle) {
    return NextResponse.json({ error: "User not found." }, { status: 404 });
  }
  return NextResponse.json({ ok: true, ...bundle });
}
