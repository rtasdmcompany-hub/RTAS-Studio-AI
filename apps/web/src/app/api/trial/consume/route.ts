import { NextResponse } from "next/server";
import { recordFreeTrialClaim } from "@/lib/server/trial-abuse-store";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";

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
