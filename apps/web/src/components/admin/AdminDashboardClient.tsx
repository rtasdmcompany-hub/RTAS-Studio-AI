"use client";

import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card } from "@rtas/ui";
import type { AdminDashboardMetrics } from "@/lib/server/admin/metrics";

const ADMIN_KEY = "rtas_admin_secret";

type Analytics = {
  dailyUsers: Array<{ date: string; count: number }>;
  dailyGenerations: Array<{ date: string; count: number }>;
  dailyCreditsUsed: Array<{ date: string; credits: number }>;
  jobStatusBreakdown: Array<{ status: string; count: number }>;
  tierBreakdown: Array<{ tier: string; count: number }>;
};

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

export function AdminDashboardClient() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<AdminDashboardMetrics | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
  }, []);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const headers = { "x-rtas-admin-secret": adminSecret };
      const [dashRes, analyticsRes] = await Promise.all([
        fetch("/api/admin/dashboard", { headers }),
        fetch("/api/admin/analytics?days=30", { headers }),
      ]);
      const dash = (await dashRes.json()) as {
        ok?: boolean;
        error?: string;
        metrics?: AdminDashboardMetrics;
      };
      const anal = (await analyticsRes.json()) as {
        ok?: boolean;
        analytics?: Analytics;
        error?: string;
      };
      if (!dashRes.ok || !dash.ok) {
        throw new Error(dash.error ?? "Dashboard unauthorized or unavailable.");
      }
      setMetrics(dash.metrics ?? null);
      setAnalytics(anal.analytics ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load admin data.");
      setMetrics(null);
      setAnalytics(null);
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
        <h1 className="text-xl text-zinc-100">Admin access</h1>
        <p className="mt-2 text-sm text-ds-text-muted">
          Enter your RTAS admin secret to view live production metrics.
        </p>
        <form className="mt-6 space-y-3" onSubmit={unlock}>
          <input
            type="password"
            className="w-full rounded-md border border-ds-border-subtle bg-ds-surface-glass px-3 py-2 text-zinc-100"
            placeholder="RTAS_ADMIN_SECRET"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
          />
          <Button type="submit" variant="primary" className="w-full">
            Unlock dashboard
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Operations dashboard</h1>
          <p className="text-sm text-ds-text-muted">
            Live production data — users, jobs, credits, revenue estimates.
          </p>
        </div>
        <Button variant="ghost" disabled={busy} onClick={() => void load(stored)}>
          Refresh
        </Button>
      </div>

      {error && <Alert variant="error" message={error} />}

      {metrics && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Total users" value={metrics.users.total} />
            <MetricCard
              label="Active subscriptions"
              value={metrics.users.activeSubscriptions}
            />
            <MetricCard
              label="MRR estimate"
              value={`$${metrics.revenue.mrrEstimateUsd}`}
              hint={`ARR ~ $${metrics.revenue.arrEstimateUsd}`}
            />
            <MetricCard
              label="Job success rate"
              value={`${metrics.jobs.successRate}%`}
              hint={`${metrics.jobs.completed} completed / ${metrics.jobs.failed} failed`}
            />
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Queue" value={metrics.jobs.queued} />
            <MetricCard label="Running" value={metrics.jobs.running} />
            <MetricCard
              label="Credits remaining"
              value={metrics.credits.totalRemaining}
            />
            <MetricCard
              label="Credits used (jobs)"
              value={metrics.credits.totalUsedEstimate}
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Recent users</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.recentUsers.map((u) => (
                  <li key={u.id} className="flex justify-between gap-2">
                    <span className="truncate text-ds-text-muted">{u.email}</span>
                    <span className="shrink-0 text-zinc-300">{u.tier}</span>
                  </li>
                ))}
              </ul>
            </Card>
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Recent jobs</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.recentJobs.map((j) => (
                  <li key={j.id} className="flex justify-between gap-2">
                    <span className="truncate text-ds-text-muted">{j.id.slice(0, 8)}…</span>
                    <span className="shrink-0 text-zinc-300">
                      {j.status} · {j.progressPercent}%
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          </section>

          <Card className="p-4">
            <h2 className="text-lg text-zinc-100">Recent logins</h2>
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              {metrics.recentLogins.length === 0 ? (
                <li>No login events recorded yet.</li>
              ) : (
                metrics.recentLogins.map((l) => (
                  <li key={l.id}>
                    {new Date(l.createdAt).toLocaleString()} — {l.message}
                  </li>
                ))
              )}
            </ul>
          </Card>
        </>
      )}

      {analytics && (
        <Card className="p-4">
          <h2 className="text-lg text-zinc-100">30-day analytics</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs uppercase text-ds-text-muted">Tier mix</p>
              <ul className="mt-2 text-sm">
                {analytics.tierBreakdown.map((t) => (
                  <li key={t.tier}>
                    {t.tier}: {t.count}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs uppercase text-ds-text-muted">Job statuses</p>
              <ul className="mt-2 text-sm">
                {analytics.jobStatusBreakdown.map((s) => (
                  <li key={s.status}>
                    {s.status}: {s.count}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
