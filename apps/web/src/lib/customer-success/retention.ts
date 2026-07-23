/**
 * Retention Center content + insights derived from the signed-in user.
 * Reuses referral helpers from Sprint 4 marketing where present.
 */

import { getCustomerHealth } from "@/lib/customer-success/customer-health";
import { getOrCreateReferralForUser } from "@/lib/marketing/referral";

export type RetentionMilestone = {
  id: string;
  label: string;
  done: boolean;
  hint: string;
  href?: string;
};

export type FeatureTip = {
  id: string;
  title: string;
  body: string;
  href: string;
};

export const FEATURE_DISCOVERY: FeatureTip[] = [
  {
    id: "compose",
    title: "Compose in Studio",
    body: "Start from a prompt + reference still. Keep Identity Preservation authorized-only.",
    href: "/studio",
  },
  {
    id: "long-form",
    title: "Long videos auto-stitch",
    body: "Standard/Premium long clips split into 15s segments and stitch automatically.",
    href: "/how-to-use",
  },
  {
    id: "premium-4k",
    title: "Premium 4K path",
    body: "When you need cinematic masters, Premium unlocks the 4K quality tier.",
    href: "/pricing",
  },
  {
    id: "changelog",
    title: "Release notes",
    body: "See what shipped before filing duplicate feedback.",
    href: "/help/changelog",
  },
  {
    id: "affiliate",
    title: "Partner & affiliate tracks",
    body: "Agencies and creators can apply — metrics start at zero until real referrals land.",
    href: "/affiliate",
  },
];

export const LEARNING_LINKS = [
  { title: "Getting started guide", href: "/how-to-use" },
  { title: "Help Center search", href: "/help" },
  { title: "FAQ by category", href: "/help/faq" },
  { title: "Troubleshooting", href: "/help/troubleshooting" },
  { title: "Showcase references", href: "/showcase" },
  { title: "Customer Success Center", href: "/success" },
] as const;

export async function getRetentionBundle(userId: string) {
  const health = await getCustomerHealth(userId);
  if (!health) return null;

  const milestones: RetentionMilestone[] = [
    {
      id: "verified",
      label: "Email verified",
      done: health.emailVerified,
      hint: health.emailVerified ? "Verified" : "Confirm the link in your inbox",
      href: health.emailVerified ? undefined : "/auth/check-email",
    },
    {
      id: "project",
      label: "First project",
      done: health.projectCount > 0,
      hint:
        health.projectCount > 0
          ? `${health.projectCount} project(s)`
          : "Save a compose in Studio",
      href: health.projectCount > 0 ? undefined : "/studio",
    },
    {
      id: "video",
      label: "First completed video",
      done: health.completedVideoCount > 0,
      hint:
        health.completedVideoCount > 0
          ? `${health.completedVideoCount} completed`
          : "Finish your first render",
      href: health.completedVideoCount > 0 ? undefined : "/studio",
    },
    {
      id: "paid",
      label: "Active subscription",
      done: health.subscription.active,
      hint: health.subscription.active
        ? `${health.subscription.tier} · active`
        : "Choose Tester, Standard, or Premium",
      href: health.subscription.active ? undefined : "/pricing",
    },
    {
      id: "habit",
      label: "Recent usage (14d)",
      done: health.usageTrend.some((d) => d.generations > 0),
      hint: health.usageTrend.some((d) => d.generations > 0)
        ? "Generations recorded in the last 14 days"
        : "No generations in the last 14 days",
      href: "/studio",
    },
  ];

  const upgradeHint =
    health.subscription.tier === "tester" || !health.subscription.active
      ? {
          title: "Upgrade when you need more seconds",
          body: "Standard $89/mo or Premium 4K $249/mo — both include 2000 seconds.",
          href: "/pricing",
        }
      : health.subscription.tier === "standard"
        ? {
            title: "Consider Premium 4K",
            body: "Same 2000s pool with cinematic 4K output for client-facing masters.",
            href: "/pricing",
          }
        : {
            title: "You are on Premium",
            body: "Use Retention tips and Help articles to maximize credit ROI.",
            href: "/help",
          };

  let referral = null;
  try {
    referral = await getOrCreateReferralForUser(userId);
  } catch {
    referral = null;
  }

  return {
    health,
    milestones,
    upgradeHint,
    featureDiscovery: FEATURE_DISCOVERY,
    learning: LEARNING_LINKS,
    referral,
    churnRecommendations: health.recommendations,
  };
}
