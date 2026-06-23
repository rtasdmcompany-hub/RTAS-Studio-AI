import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import {
  getTesterSubscription,
  resetTesterSubscriptionForDev,
} from "@/lib/server/tester-subscription";

export const runtime = "nodejs";

export async function POST() {
  if (process.env.NODE_ENV !== "development") {
    return NextResponse.json({ error: "Not available in production." }, { status: 403 });
  }

  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const updated = await resetTesterSubscriptionForDev(userId);
  if (!updated) {
    const current = await getTesterSubscription(userId);
    if (!current) {
      return NextResponse.json(
        { error: "No tester subscription found for this account." },
        { status: 404 }
      );
    }
  }

  if (!updated) {
    return NextResponse.json({ error: "Could not reset tester subscription." }, { status: 500 });
  }

  return NextResponse.json({
    ok: true,
    testerSubscription: {
      id: updated.id,
      secondsUsed: updated.secondsUsed,
      remainingSeconds: Math.max(0, updated.allowedSeconds - updated.secondsUsed),
      allowedSeconds: updated.allowedSeconds,
      endDate: updated.endDate.toISOString(),
      isActive: updated.isActive,
    },
  });
}
