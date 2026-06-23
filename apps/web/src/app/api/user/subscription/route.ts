import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { applyCreditExpiry } from "@/lib/store";
import { authOptions } from "@/lib/auth/auth-options";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";
import {
  getUserRenderingState,
  listRecentGenerationJobs,
  MAX_CONCURRENT_TRACKS,
} from "@/lib/server/studio-generation-guard";

export const runtime = "nodejs";

const AUTH_REQUIRED_BODY = {
  error: "Authentication required. Please log in to access the studio.",
} as const;

/** Client syncs Studio subscription/credits after MoR checkout / webhook */
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json(AUTH_REQUIRED_BODY, { status: 401 });
  }

  const userId = session.user.id;

  let profile = await getServerProfile(userId);
  const expired = applyCreditExpiry(profile);
  if (expired.credits !== profile.credits) {
    profile = await saveServerProfile(expired);
  }

  const renderingState = await getUserRenderingState(userId);
  const recentJobs = await listRecentGenerationJobs(userId, 3);

  return NextResponse.json({
    tier: profile.tier,
    subscriptionActive: profile.subscriptionActive,
    credits: renderingState.credits,
    creditsExpireAt: profile.creditsExpireAt,
    subscriptionRenewsAt: profile.subscriptionRenewsAt,
    paymentProvider: profile.paymentProvider,
    freeTrialUsed: profile.freeTrialUsed,
    hasUsedFreeTrial: profile.hasUsedFreeTrial ?? profile.freeTrialUsed,
    studioMetrics: {
      renderingQueues: renderingState.concurrentTracks,
      concurrentTracks: renderingState.concurrentTracks,
      maxConcurrentGenerations: MAX_CONCURRENT_TRACKS,
      videoGenerationCredits: renderingState.credits,
      recentJobs,
    },
  });
}

/** Dev-only studio metrics snapshot */
export async function POST() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json(AUTH_REQUIRED_BODY, { status: 401 });
  }

  if (process.env.NODE_ENV !== "development") {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const userId = session.user.id;
  const renderingState = await getUserRenderingState(userId);
  const recentJobs = await listRecentGenerationJobs(userId, 5);

  return NextResponse.json({
    ok: true,
    studioMetrics: {
      renderingQueues: renderingState.concurrentTracks,
      concurrentTracks: renderingState.concurrentTracks,
      maxConcurrentGenerations: MAX_CONCURRENT_TRACKS,
      videoGenerationCredits: renderingState.credits,
      recentJobs,
    },
  });
}
