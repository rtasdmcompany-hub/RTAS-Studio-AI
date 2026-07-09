import { NextResponse } from "next/server";
import {
  FREE_TRIAL_ABUSE_MESSAGE,
  isFreeTrialBlocked,
} from "@/lib/server/trial-abuse-store";
import { getServerProfile } from "@/lib/server/profile-store";
import {
  clientIpFromRequest,
  requireApiSession,
} from "@/lib/server/api-auth";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  let body: { deviceFingerprint?: string } = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const userId = auth.userId;
  const deviceFingerprint = body.deviceFingerprint?.trim() ?? "";
  const ipAddress = clientIpFromRequest(request);

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
