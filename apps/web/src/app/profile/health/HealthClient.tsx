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
import type { CustomerHealthSnapshot } from "@/lib/customer-success/customer-health";

export function HealthClient() {
  const { status } = useSession();
  const [health, setHealth] = useState<CustomerHealthSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch("/api/user/health");
      const data = (await res.json()) as {
        ok?: boolean;
        health?: CustomerHealthSnapshot;
        error?: string;
      };
      if (!res.ok) throw new Error(data.error || "Could not load health.");
      setHealth(data.health ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load health.");
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
            <h1 className="text-zinc-100">Customer Health</h1>
            <p className="mt-3 text-ds-text-muted">Sign in to view your account health.</p>
            <ButtonLink
              href="/auth/login?callbackUrl=/profile/health"
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
            <Link href="/profile" className="text-ds-accent-lavender">
              Dashboard
            </Link>{" "}
            · Health
          </p>
          <h1 className="text-zinc-100">Customer Health Dashboard</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Signals from your account only. Risk level is rule-based — not a predictive AI
            score and never invented for other customers.
          </p>
        </InnerPageSection>

        {error ? (
          <Alert variant="error" message={error} onDismiss={() => setError(null)} />
        ) : null}

        {health ? (
          <>
            <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[
                { label: "Account age", value: `${health.accountAgeDays} days` },
                {
                  label: "Email verified",
                  value: health.emailVerified ? "Yes" : "No",
                },
                {
                  label: "Subscription",
                  value: `${health.subscription.tier}${
                    health.subscription.active ? " · active" : " · inactive"
                  }`,
                },
                { label: "Credits", value: `${health.credits}s` },
                { label: "Projects", value: String(health.projectCount) },
                {
                  label: "Videos",
                  value: `${health.completedVideoCount} completed / ${health.videoCount} total`,
                },
                {
                  label: "Last login",
                  value: health.lastLoginAt
                    ? new Date(health.lastLoginAt).toLocaleString()
                    : "Not recorded yet",
                },
                {
                  label: "Last generation",
                  value: health.lastGenerationAt
                    ? new Date(health.lastGenerationAt).toLocaleString()
                    : "None yet",
                },
                {
                  label: "Tickets",
                  value: `${health.openTicketCount} open / ${health.totalTicketCount} total`,
                },
                {
                  label: "Risk level",
                  value: `${health.riskLevel} (${health.riskScore})`,
                },
              ].map((card) => (
                <InnerPageSection key={card.label}>
                  <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                    {card.label}
                  </p>
                  <p className="mt-2 text-lg text-zinc-100">{card.value}</p>
                </InnerPageSection>
              ))}
            </section>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Usage trend (14 days)</h2>
              <ul className="mt-4 space-y-1 font-mono text-xs text-ds-text-muted">
                {health.usageTrend.map((d) => (
                  <li key={d.date}>
                    {d.date}: {d.generations} gen · {d.creditsCharged} credits
                  </li>
                ))}
              </ul>
            </InnerPageSection>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Signals</h2>
              <ul className="mt-4 space-y-3">
                {health.signals.map((s) => (
                  <li key={s.id}>
                    <p className="font-medium text-zinc-100">
                      [{s.severity}] {s.label}
                    </p>
                    <p className="text-sm text-ds-text-muted">{s.detail}</p>
                  </li>
                ))}
              </ul>
            </InnerPageSection>

            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Recommendations</h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ds-text-muted">
                {health.recommendations.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
              <div className="mt-6 flex flex-wrap gap-3">
                <ButtonLink href="/retention" variant="lavender">
                  Retention Center
                </ButtonLink>
                <ButtonLink href="/tickets" variant="ghost">
                  Support tickets
                </ButtonLink>
              </div>
            </InnerPageSection>
          </>
        ) : !error ? (
          <InnerPageSection>
            <p className="text-ds-text-muted">Loading health…</p>
          </InnerPageSection>
        ) : null}
      </InnerPageContainer>
    </MarketingLayout>
  );
}
