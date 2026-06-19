import { NextResponse } from "next/server";
import { applyCreditExpiry } from "@/lib/store";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";

export const runtime = "nodejs";

/** Client syncs Premium status after MoR checkout / webhook */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get("userId") ?? "local-user";

  let profile = await getServerProfile(userId);
  const expired = applyCreditExpiry(profile);
  if (expired.credits !== profile.credits) {
    profile = await saveServerProfile(expired);
  }

  return NextResponse.json({
    tier: profile.tier,
    subscriptionActive: profile.subscriptionActive,
    credits: profile.credits,
    creditsExpireAt: profile.creditsExpireAt,
    subscriptionRenewsAt: profile.subscriptionRenewsAt,
    paymentProvider: profile.paymentProvider,
    freeTrialUsed: profile.freeTrialUsed,
    hasUsedFreeTrial: profile.hasUsedFreeTrial ?? profile.freeTrialUsed,
  });
}
