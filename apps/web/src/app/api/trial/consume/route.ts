import { NextResponse } from "next/server";
import { recordFreeTrialClaim } from "@/lib/server/trial-abuse-store";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";
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

  await recordFreeTrialClaim({ userId, ipAddress, deviceFingerprint });

  const profile = await getServerProfile(userId);
  const updated = await saveServerProfile({
    ...profile,
    freeTrialUsed: true,
    hasUsedFreeTrial: true,
    ipAddress: ipAddress || profile.ipAddress || null,
    deviceFingerprint: deviceFingerprint || profile.deviceFingerprint || null,
  });

  return NextResponse.json({
    ok: true,
    freeTrialUsed: updated.freeTrialUsed,
    hasUsedFreeTrial: updated.hasUsedFreeTrial,
  });
}
