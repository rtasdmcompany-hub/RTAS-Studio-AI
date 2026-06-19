import { NextResponse } from "next/server";
import {
  FREE_TRIAL_ABUSE_MESSAGE,
  isFreeTrialBlocked,
} from "@/lib/server/trial-abuse-store";
import { getServerProfile } from "@/lib/server/profile-store";

export const runtime = "nodejs";

function clientIp(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0]?.trim() ?? "";
  return request.headers.get("x-real-ip")?.trim() ?? "";
}

export async function POST(request: Request) {
  let body: { userId?: string; deviceFingerprint?: string } = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const userId = body.userId?.trim() || "local-user";
  const deviceFingerprint = body.deviceFingerprint?.trim() ?? "";
  const ipAddress = clientIp(request);

  const profile = await getServerProfile(userId);

  if (profile.subscriptionActive && profile.credits > 0) {
    return NextResponse.json({ allowed: true, premium: true });
  }

  const accountTrialUsed =
    profile.hasUsedFreeTrial ?? profile.freeTrialUsed ?? false;

  const result = await isFreeTrialBlocked({
    userId,
    ipAddress,
    deviceFingerprint,
    accountTrialUsed,
  });

  if (result.blocked) {
    return NextResponse.json(
      {
        allowed: false,
        reason: result.reason,
        message: FREE_TRIAL_ABUSE_MESSAGE,
      },
      { status: 403 }
    );
  }

  return NextResponse.json({ allowed: true });
}
