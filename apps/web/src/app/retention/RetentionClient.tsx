"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { Alert, ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

type RetentionPayload = {
  health: {
    credits: number;
    riskLevel: string;
    riskScore: number;
    completedVideoCount: number;
    projectCount: number;
    subscription: { tier: string; active: boolean };
    usageTrend: Array<{ date: string; generations: number; creditsCharged: number }>;
  };
  milestones: Array<{
    id: string;
    label: string;
    done: boolean;
    hint: string;
    href?: string;
  }>;
  upgradeHint: { title: string; body: string; href: string };
  featureDiscovery: Array<{ id: string; title: string; body: string; href: string }>;
  learning: Array<{ title: string; href: string }>;
  churnRecommendations: string[];
  referral: {
    programStatus: string;
    code: string | null;
    link: string | null;
    invitesSent: number;
    signedUp: number;
    converted: number;
    proposedRewards: { referrerCredits: number; referredCredits: number; note: string };
  } | null;
};

export function RetentionClient() {
  const { status } = useSession();
  const [data, setData] = useState<RetentionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch("/api/user/retention");
      const json = (await res.json()) as RetentionPayload & {
        ok?: boolean;
        error?: string;
      };
      if (!res.ok) throw new Error(json.error || "Could not load retention data.");
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load retention data.");
    }
  }, []);

  useEffect(() => {
    if (status === "authenticated") void load();
  }, [status, load]);

  if (status !== "authenticated") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection className="text-center">
            <h1 className="text-zinc-100">Retention Center</h1>
            <p className="mt-3 text-ds-text-muted">
              Sign in to see your usage insights and milestones — never fabricated.
            </p>
            <ButtonLink
              href="/auth/login?callbackUrl=/retention"
              variant="lavender"
              className="mt-6"
            >
              Sign in
            </ButtonLink>
          </InnerPageSection>
        </InnerPageContainer>
      </MarketingLayout>
    );
  }

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/success" className="text-ds-accent-lavender">
              Success Center
            </Link>
          </p>
          <h1 className="text-zinc-100">Retention Center</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Insights, upgrades, feature discovery, learning, referral, and milestones from
            your account. Churn tips are rule-based — not AI predictions.
          </p>
        </InnerPageSection>

        {error ? (
          <Alert variant="error" message={error} onDismiss={() => setError(null)} />
        ) : null}

        {data ? (
          <>
            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Usage snapshot</h2>
              <p className="mt-2 text-sm text-ds-text-muted">
                {data.health.credits}s credits · {data.health.projectCount} projects ·{" "}
                {data.health.completedVideoCount} completed videos · risk{" "}
                {data.health.riskLevel} ({data.health.riskScore}) · plan{" "}
                {data.health.subscription.tier}
                {data.health.subscription.active ? " · active" : " · inactive"}
              </p>
              <p className="mt-4 text-sm text-ds-text-muted">
                Last 14 days generations:{" "}
                {data.health.usageTrend.reduce((n, d) => n + d.generations, 0)} · credits
                charged:{" "}
                {data.health.usageTrend.reduce((n, d) => n + d.creditsCharged, 0)}
              </p>
              <div className="mt-4">
                <ButtonLink href="/profile/health" variant="ghost">
                  Full health dashboard →
                </ButtonLink>
              </div>
            </InnerPageSection>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Milestones</h2>
              <ul className="mt-4 space-y-3">
                {data.milestones.map((m) => (
                  <li key={m.id} className="flex flex-wrap items-center gap-3 text-sm">
                    <span aria-hidden>{m.done ? "✓" : "○"}</span>
                    <span className="text-zinc-100">{m.label}</span>
                    <span className="text-ds-text-muted">{m.hint}</span>
                    {!m.done && m.href ? (
                      <Link
                        href={m.href}
                        className="text-ds-accent-lavender underline-offset-2 hover:underline"
                      >
                        Continue →
                      </Link>
                    ) : null}
                  </li>
                ))}
              </ul>
            </InnerPageSection>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">{data.upgradeHint.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{data.upgradeHint.body}</p>
              <div className="mt-4">
                <ButtonLink href={data.upgradeHint.href} variant="lavender">
                  View pricing
                </ButtonLink>
              </div>
            </InnerPageSection>

            <section className="grid gap-4 md:grid-cols-2">
              {data.featureDiscovery.map((f) => (
                <InnerPageSection key={f.id}>
                  <h3 className="text-lg text-zinc-100">{f.title}</h3>
                  <p className="mt-2 text-sm text-ds-text-muted">{f.body}</p>
                  <div className="mt-4">
                    <ButtonLink href={f.href} variant="ghost">
                      Open →
                    </ButtonLink>
                  </div>
                </InnerPageSection>
              ))}
            </section>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Learning & tutorials</h2>
              <ul className="mt-4 space-y-2 text-sm">
                {data.learning.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="text-ds-accent-lavender underline-offset-2 hover:underline"
                    >
                      {l.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </InnerPageSection>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Recovery recommendations</h2>
              {data.churnRecommendations.length === 0 ? (
                <p className="mt-2 text-sm text-ds-text-muted">No recommendations right now.</p>
              ) : (
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
                  {data.churnRecommendations.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              )}
            </InnerPageSection>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Referral</h2>
              {data.referral?.code ? (
                <>
                  <p className="mt-2 text-sm text-ds-text-muted">
                    Code <span className="text-zinc-100">{data.referral.code}</span> · status{" "}
                    {data.referral.programStatus} · invites {data.referral.invitesSent} ·
                    signed up {data.referral.signedUp} · converted {data.referral.converted}
                  </p>
                  <p className="mt-2 text-xs text-ds-text-muted">
                    {data.referral.proposedRewards.note}
                  </p>
                  {data.referral.link ? (
                    <p className="mt-2 break-all text-sm text-ds-accent-lavender">
                      {data.referral.link}
                    </p>
                  ) : null}
                </>
              ) : (
                <p className="mt-2 text-sm text-ds-text-muted">
                  Referral code will appear when the database is available.
                </p>
              )}
            </InnerPageSection>
          </>
        ) : !error ? (
          <InnerPageSection>
            <p className="text-ds-text-muted">Loading your retention data…</p>
          </InnerPageSection>
        ) : null}
      </InnerPageContainer>
    </MarketingLayout>
  );
}
