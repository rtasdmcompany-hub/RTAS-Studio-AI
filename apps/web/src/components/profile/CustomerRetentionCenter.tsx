"use client";

import { useEffect } from "react";
import Link from "next/link";
import type { UserProfile } from "@rtas/shared";
import {
  PREMIUM_PRICE_USD,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { RELEASE_NOTES, PRODUCT_VERSION } from "@/lib/release-notes";
import {
  deriveLifecycleStage,
  lifecycleNextAction,
  LIFECYCLE_STAGE_LABEL,
  type LifecycleSignals,
} from "@/lib/customer-lifecycle";
import { trackClientEvent } from "@/lib/analytics";
import { AnalyticsEvents } from "@/lib/analytics/events";

type Props = {
  profile: UserProfile;
  recentJobCount: number;
  completedVideoCount: number;
  emailVerified: boolean;
};

function suggestUpgrade(profile: UserProfile): {
  title: string;
  body: string;
  href: string;
  cta: string;
} | null {
  if (profile.tier === "premium" && profile.subscriptionActive) {
    return null;
  }
  if (profile.tier === "standard" && profile.subscriptionActive) {
    return {
      title: "Consider Premium 4K",
      body: `When you need cinematic 4K masters, Premium is $${PREMIUM_PRICE_USD}/mo with the same credit clarity (1 credit = 1 second).`,
      href: "/pricing#plans",
      cta: "Compare Premium 4K",
    };
  }
  if (profile.tier === "tester" || (profile.credits > 0 && !profile.subscriptionActive)) {
    return {
      title: "Ready for a monthly plan?",
      body: `Standard ($${STANDARD_PRICE_USD}/mo) unlocks HD commercial downloads. No fake urgency — upgrade when your pipeline needs it.`,
      href: "/pricing#plans",
      cta: "View upgrade options",
    };
  }
  if (profile.credits <= 0) {
    return {
      title: "Add credits to keep creating",
      body: `New accounts start at 0 credits. Tester is $${TESTER_PRICE_USD} for a short evaluation — not a free credit plan.`,
      href: "/pricing#plans",
      cta: "Get Tester",
    };
  }
  return {
    title: "Explore plans",
    body: "Compare Tester, Standard, and Premium 4K with transparent second-based credits.",
    href: "/pricing#plans",
    cta: "Compare plans",
  };
}

/**
 * Customer Retention Center — usage, credits, learning, support, proposed referral.
 * Uses this account’s real data only.
 */
export function CustomerRetentionCenter({
  profile,
  recentJobCount,
  completedVideoCount,
  emailVerified,
}: Props) {
  const signals: LifecycleSignals = {
    hasAccount: Boolean(profile.id),
    emailVerified,
    hasProjectOrJob: recentJobCount > 0,
    hasCompletedVideo: completedVideoCount > 0,
    hasPaidPlan:
      profile.subscriptionActive ||
      profile.tier === "tester" ||
      profile.tier === "standard" ||
      profile.tier === "premium",
    subscriptionActive: profile.subscriptionActive,
    credits: profile.credits,
    expanded: profile.tier === "premium" && profile.subscriptionActive,
    churnRisk:
      (profile.tier === "tester" ||
        profile.tier === "standard" ||
        profile.tier === "premium") &&
      profile.credits <= 0 &&
      !profile.subscriptionActive,
    looksChurned:
      (profile.tier === "standard" || profile.tier === "premium") &&
      !profile.subscriptionActive &&
      profile.credits <= 0,
  };

  const stage = deriveLifecycleStage(signals);
  const next = lifecycleNextAction(stage);
  const upgrade = suggestUpgrade(profile);
  const latestRelease = RELEASE_NOTES[0];

  useEffect(() => {
    trackClientEvent(AnalyticsEvents.RETENTION_CENTER_VIEWED, {
      stage,
      tier: profile.tier,
      credits: profile.credits,
    });
    trackClientEvent(AnalyticsEvents.LIFECYCLE_STAGE, { stage });
  }, [stage, profile.tier, profile.credits]);

  return (
    <section
      className="dashboard-section dashboard-retention"
      id="retention-center"
      aria-labelledby="dash-retention"
    >
      <div className="dashboard-section__head">
        <h2 id="dash-retention">Customer Retention Center</h2>
        <p className="dashboard-section__sub">
          Your account only — lifecycle stage{" "}
          <strong>{LIFECYCLE_STAGE_LABEL[stage]}</strong>. No invented team metrics.
        </p>
      </div>

      <div className="dashboard-retention__grid">
        <article className="dashboard-retention__card">
          <h3>Usage summary</h3>
          <ul>
            <li>
              Remaining credits: <strong>{profile.credits}s</strong> (1 credit = 1
              second)
            </li>
            <li>
              Plan: <strong>{profile.tier}</strong>
              {profile.subscriptionActive ? " · active" : " · inactive"}
            </li>
            <li>Recent jobs in view: {recentJobCount}</li>
            <li>Completed videos in view: {completedVideoCount}</li>
          </ul>
          <ButtonLink href={next.href} variant="lavender">
            {next.label}
          </ButtonLink>
        </article>

        {upgrade ? (
          <article className="dashboard-retention__card">
            <h3>{upgrade.title}</h3>
            <p>{upgrade.body}</p>
          <ButtonLink href={upgrade.href} variant="ghost">
              {upgrade.cta}
            </ButtonLink>
          </article>
        ) : (
          <article className="dashboard-retention__card">
            <h3>You’re on Premium 4K</h3>
            <p>
              Thanks for shipping on the top self-serve plan. Reach Customer Success
              anytime for team workflows.
            </p>
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
          </article>
        )}

        <article className="dashboard-retention__card">
          <h3>Release notes</h3>
          <p>
            v{PRODUCT_VERSION}
            {latestRelease
              ? ` · ${latestRelease.date} — ${latestRelease.summary.slice(0, 120)}…`
              : null}
          </p>
          <Link href="/help/changelog" className="dashboard-success__cta">
            Full changelog →
          </Link>
        </article>

        <article className="dashboard-retention__card">
          <h3>Learning & support</h3>
          <ul className="dashboard-retention__links">
            <li>
              <Link href="/how-to-use">How to use</Link>
            </li>
            <li>
              <Link href="/docs">Documentation</Link>
            </li>
            <li>
              <Link href="/help">Help Center</Link>
            </li>
            <li>
              <Link href="/success">Success Center</Link>
            </li>
            <li>
              <Link href="/retention">Retention Center</Link>
            </li>
            <li>
              <Link href="/profile/health">Customer Health</Link>
            </li>
            <li>
              <Link href="/tickets">Support tickets</Link>
            </li>
            <li>
              <Link href="/help/contact">Contact support</Link>
            </li>
            <li>
              <Link href="/feedback">Send feedback</Link>
            </li>
          </ul>
        </article>

        <article className="dashboard-retention__card dashboard-retention__card--proposed">
          <p className="dashboard-retention__badge">Proposed</p>
          <h3>Referral invitation</h3>
          <p>
            Referral rewards are not live yet. When the program launches, you will invite
            creators from this panel. Until then, share{" "}
            <Link href="/">rtasstudio.com</Link> with peers — no fabricated referral
            credits.
          </p>
        </article>
      </div>
    </section>
  );
}
