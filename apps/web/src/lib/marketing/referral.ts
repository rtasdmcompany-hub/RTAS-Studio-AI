/**
 * Studio referral program helpers — Proposed rewards until billing credits live rewards.
 */

import { createHash, randomBytes } from "crypto";
import { isPrismaConfigured, prisma } from "@/lib/prisma";
import { getMarketingAppUrl } from "@/lib/marketing/email-layout";

export const REFERRAL_PROGRAM_STATUS = "proposed" as const;

/** Proposed reward — not auto-granted until ops enables. */
export const PROPOSED_REFERRAL_REWARDS = {
  referrerCredits: 30,
  referredCredits: 15,
  note: "Proposed — credits are not auto-granted until reward engine is enabled.",
} as const;

export type ReferralSummary = {
  programStatus: typeof REFERRAL_PROGRAM_STATUS;
  code: string | null;
  link: string | null;
  invitesSent: number;
  signedUp: number;
  converted: number;
  rewardsGranted: number;
  proposedRewards: typeof PROPOSED_REFERRAL_REWARDS;
  history: Array<{
    id: string;
    referredEmail: string;
    status: string;
    invitedAt: string;
    signedUpAt: string | null;
    rewardedAt: string | null;
  }>;
};

function makeCode(userId: string): string {
  const salt = randomBytes(3).toString("hex");
  const hash = createHash("sha256").update(`${userId}:${salt}`).digest("hex").slice(0, 6);
  return `RTAS-${hash.toUpperCase()}`;
}

export async function getOrCreateReferralForUser(userId: string): Promise<ReferralSummary> {
  const empty: ReferralSummary = {
    programStatus: REFERRAL_PROGRAM_STATUS,
    code: null,
    link: null,
    invitesSent: 0,
    signedUp: 0,
    converted: 0,
    rewardsGranted: 0,
    proposedRewards: PROPOSED_REFERRAL_REWARDS,
    history: [],
  };

  if (!isPrismaConfigured()) return empty;

  try {
    let account = await prisma.studioReferralCode.findUnique({ where: { userId } });
    if (!account) {
      const code = makeCode(userId);
      account = await prisma.studioReferralCode.create({
        data: {
          userId,
          code,
          link: `${getMarketingAppUrl()}/auth/register?ref=${encodeURIComponent(code)}`,
          active: true,
        },
      });
    }

    const referrals = await prisma.studioReferral.findMany({
      where: { referrerUserId: userId },
      orderBy: { invitedAt: "desc" },
      take: 50,
    });

    return {
      programStatus: REFERRAL_PROGRAM_STATUS,
      code: account.code,
      link: account.link || `${getMarketingAppUrl()}/auth/register?ref=${account.code}`,
      invitesSent: referrals.length,
      signedUp: referrals.filter((r) => r.status === "signed_up" || r.signedUpAt).length,
      converted: referrals.filter((r) => r.status === "converted" || r.convertedAt).length,
      rewardsGranted: referrals.filter((r) => Boolean(r.rewardedAt)).length,
      proposedRewards: PROPOSED_REFERRAL_REWARDS,
      history: referrals.map((r) => ({
        id: r.id,
        referredEmail: r.referredEmail || "(pending)",
        status: r.status,
        invitedAt: r.invitedAt.toISOString(),
        signedUpAt: r.signedUpAt?.toISOString() ?? null,
        rewardedAt: r.rewardedAt?.toISOString() ?? null,
      })),
    };
  } catch {
    return empty;
  }
}

export async function inviteReferral(input: {
  referrerUserId: string;
  email: string;
}): Promise<{ ok: true; referralId: string } | { ok: false; error: string }> {
  if (!isPrismaConfigured()) {
    return { ok: false, error: "Database not configured." };
  }
  const email = input.email.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return { ok: false, error: "Valid email required." };
  }

  try {
    const summary = await getOrCreateReferralForUser(input.referrerUserId);
    if (!summary.code) {
      return { ok: false, error: "Could not allocate referral code." };
    }
    const codeRow = await prisma.studioReferralCode.findUnique({
      where: { userId: input.referrerUserId },
    });
    if (!codeRow) return { ok: false, error: "Referral code missing." };

    const row = await prisma.studioReferral.create({
      data: {
        referralCodeId: codeRow.id,
        code: codeRow.code,
        referrerUserId: input.referrerUserId,
        referredEmail: email,
        status: "invited",
        rewardCredits: PROPOSED_REFERRAL_REWARDS.referrerCredits,
        referredBonusCredits: PROPOSED_REFERRAL_REWARDS.referredCredits,
      },
    });
    return { ok: true, referralId: row.id };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Invite failed.",
    };
  }
}
