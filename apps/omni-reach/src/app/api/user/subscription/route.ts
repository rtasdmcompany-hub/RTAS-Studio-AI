import { NextResponse } from "next/server";
import { applyCreditExpiry } from "@/lib/store";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";
import { getTesterSubscription } from "@/lib/server/tester-subscription";

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

  const testerSubscription = await getTesterSubscription(userId);
  const testerEndDate = testerSubscription?.endDate ?? null;
  const testerIsActive =
    Boolean(testerSubscription?.isActive) &&
    testerEndDate !== null &&
    testerEndDate > new Date();
  const testerRemainingSeconds = testerSubscription
    ? Math.max(0, testerSubscription.allowedSeconds - testerSubscription.secondsUsed)
    : null;

  return NextResponse.json({
    tier: profile.tier,
    subscriptionActive: profile.subscriptionActive,
    credits: profile.credits,
    creditsExpireAt: profile.creditsExpireAt,
    subscriptionRenewsAt: profile.subscriptionRenewsAt,
    paymentProvider: profile.paymentProvider,
    freeTrialUsed: profile.freeTrialUsed,
    hasUsedFreeTrial: profile.hasUsedFreeTrial ?? profile.freeTrialUsed,
    testerSubscription: testerSubscription
      ? {
          id: testerSubscription.id,
          allowedSeconds: testerSubscription.allowedSeconds,
          secondsUsed: testerSubscription.secondsUsed,
          remainingSeconds: testerRemainingSeconds,
          endDate: testerSubscription.endDate.toISOString(),
          isActive: testerIsActive,
        }
      : null,
  });
}
