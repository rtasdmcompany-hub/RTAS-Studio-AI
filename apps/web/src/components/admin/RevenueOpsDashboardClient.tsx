"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Alert, Button, Card } from "@rtas/ui";
import type { RevenueOpsMetrics } from "@/lib/server/admin/revenue-metrics";

const ADMIN_KEY = "rtas_admin_secret";

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card className="p-4">
      <p className="text-xs uppercase tracking-wide text-ds-text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-zinc-100">{value}</p>
      {hint ? <p className="mt-1 text-xs text-ds-text-muted">{hint}</p> : null}
    </Card>
  );
}

export function RevenueOpsDashboardClient() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<RevenueOpsMetrics | null>(null);

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
  }, []);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/revenue", {
        headers: { "x-rtas-admin-secret": adminSecret },
      });
      const data = (await res.json()) as {
        ok?: boolean;
        error?: string;
        metrics?: RevenueOpsMetrics;
      };
      if (!res.ok || !data.ok) {
        throw new Error(data.error ?? "Revenue dashboard unauthorized or unavailable.");
      }
      setMetrics(data.metrics ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load revenue data.");
      setMetrics(null);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (stored) void load(stored);
  }, [stored, load]);

  function unlock(e: React.FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;
    sessionStorage.setItem(ADMIN_KEY, secret.trim());
    setStored(secret.trim());
  }

  if (!stored) {
    return (
      <div className="mx-auto max-w-md p-6">
        <h1 className="text-xl text-zinc-100">Revenue ops access</h1>
        <p className="mt-2 text-sm text-ds-text-muted">
          Enter your RTAS admin secret to view live RevOps metrics.
        </p>
        <form className="mt-6 space-y-3" onSubmit={unlock}>
          <input
            type="password"
            className="w-full rounded-md border border-ds-border-subtle bg-ds-surface-glass px-3 py-2 text-zinc-100"
            placeholder="RTAS_ADMIN_SECRET"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            autoComplete="current-password"
          />
          <Button type="submit" variant="primary" className="w-full">
            Unlock revenue dashboard
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Revenue operations</h1>
          <p className="text-sm text-ds-text-muted">
            Live aggregates only — zeros are valid. No fabricated MRR, customers, or funnel %.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/admin" className="rtas-btn-ghost rtas-ui-btn">
            Ops dashboard
          </Link>
          <Button variant="ghost" disabled={busy} onClick={() => void load(stored)}>
            Refresh
          </Button>
        </div>
      </div>

      {error && <Alert variant="error" message={error} />}

      {metrics && (
        <>
          <p className="text-xs text-ds-text-muted">{metrics.integrityNote}</p>
          <p className="text-xs text-ds-text-muted">
            Generated {new Date(metrics.generatedAt).toLocaleString()}
          </p>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Signups">
            <MetricCard label="New signups (today)" value={metrics.signups.newToday} />
            <MetricCard label="New signups (7d)" value={metrics.signups.newThisWeek} />
            <MetricCard label="New signups (month)" value={metrics.signups.newThisMonth} />
            <MetricCard label="Total users" value={metrics.signups.total} />
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Verification & paid">
            <MetricCard
              label="Verified"
              value={metrics.verified.count}
              hint={`${metrics.verified.unverified} unverified`}
            />
            <MetricCard
              label="Free (unpaid)"
              value={metrics.unpaid.freeUnpaid}
              hint="tier=free · no active sub"
            />
            <MetricCard
              label="Paid signals"
              value={metrics.paid.anyPaidSignal}
              hint={`${metrics.paid.activeSubscriptions} active subs`}
            />
            <MetricCard
              label="Support tickets"
              value={metrics.supportTickets.total}
              hint={`Feedback ${metrics.supportTickets.feedbackSubmissions} · Leads ${metrics.supportTickets.commercialLeads + metrics.supportTickets.marketingLeads}`}
            />
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Revenue">
            <MetricCard
              label="MRR"
              value={`$${metrics.revenue.mrrUsd}`}
              hint="Active Standard + Premium only"
            />
            <MetricCard label="ARR" value={`$${metrics.revenue.arrUsd}`} hint="MRR × 12" />
            <MetricCard
              label="Tester one-time (est.)"
              value={`$${metrics.revenue.testerOneTimeEstimateUsd}`}
              hint="Excluded from MRR"
            />
            <MetricCard
              label="Ledger collected"
              value={`$${metrics.revenue.ledgerCollectedUsd}`}
              hint="BillingTransaction sum (completed)"
            />
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Credits">
            <MetricCard label="Credits remaining" value={metrics.creditUsage.totalRemaining} />
            <MetricCard
              label="Credits used (jobs)"
              value={metrics.creditUsage.totalChargedOnJobs}
            />
            <MetricCard
              label="Users with credits"
              value={metrics.creditUsage.usersWithCredits}
            />
            <MetricCard
              label="Users at 0 credits"
              value={metrics.creditUsage.usersWithZeroCredits}
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Top plans</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.topPlans.map((p) => (
                  <li key={p.plan} className="flex justify-between gap-2">
                    <span className="text-ds-text-muted">{p.plan}</span>
                    <span className="text-zinc-300">
                      {p.count}
                      {p.mrrContributionUsd > 0
                        ? ` · $${p.mrrContributionUsd} MRR`
                        : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Subscription status</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.subscriptionStatus.map((s) => (
                  <li key={s.status} className="flex justify-between gap-2">
                    <span className="truncate text-ds-text-muted">{s.status}</span>
                    <span className="shrink-0 text-zinc-300">{s.count}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Lifecycle counts (real)</h2>
              <p className="mt-1 text-xs text-ds-text-muted">
                Derived per user from account signals — not conversion-rate charts.
              </p>
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.lifecycleCounts.length === 0 ? (
                  <li className="text-ds-text-muted">No users yet.</li>
                ) : (
                  metrics.lifecycleCounts.map((row) => (
                    <li key={row.stage} className="flex justify-between gap-2">
                      <span className="text-ds-text-muted">{row.stage}</span>
                      <span className="text-zinc-300">{row.count}</span>
                    </li>
                  ))
                )}
              </ul>
            </Card>
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Support & leads</h2>
              <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
                <li>Product feedback: {metrics.supportTickets.feedbackSubmissions}</li>
                <li>Commercial leads: {metrics.supportTickets.commercialLeads}</li>
                <li>Marketing leads: {metrics.supportTickets.marketingLeads}</li>
              </ul>
            </Card>
          </section>

          <Card className="p-4">
            <h2 className="text-lg text-zinc-100">Recent transactions</h2>
            {metrics.recentTransactions.length === 0 ? (
              <p className="mt-3 text-sm text-ds-text-muted">
                No billing ledger rows yet. When Paddle/Lemon webhooks write
                BillingTransaction records, they appear here.
              </p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.recentTransactions.map((t) => (
                  <li key={t.id} className="flex flex-wrap justify-between gap-2">
                    <span className="text-ds-text-muted">
                      {new Date(t.createdAt).toLocaleString()} · {t.provider} ·{" "}
                      {t.eventType}
                    </span>
                    <span className="text-zinc-300">
                      ${t.amountUsd}
                      {t.planKey ? ` · ${t.planKey}` : ""} · {t.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
