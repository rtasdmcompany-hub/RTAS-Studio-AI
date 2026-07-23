"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card } from "@rtas/ui";
import {
  AdminMetricCard,
  AdminPageShell,
  formatPct,
  formatUsd,
  useAdminSecret,
} from "@/components/admin/AdminShell";
import type { ExecutiveKpis, PeriodKey } from "@/lib/server/admin/executive-bi";
import type { BusinessAlertsResult } from "@/lib/server/admin/business-alerts";

type TabId =
  | "overview"
  | "revenue"
  | "customer"
  | "usage"
  | "generation"
  | "infrastructure"
  | "support"
  | "enterprise"
  | "marketing"
  | "reports"
  | "alerts";

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "revenue", label: "Revenue" },
  { id: "customer", label: "Customer" },
  { id: "usage", label: "Usage" },
  { id: "generation", label: "Generation" },
  { id: "infrastructure", label: "Infrastructure" },
  { id: "support", label: "Support" },
  { id: "enterprise", label: "Enterprise" },
  { id: "marketing", label: "Marketing" },
  { id: "reports", label: "Reports" },
  { id: "alerts", label: "Alerts" },
];

const PERIODS: PeriodKey[] = [
  "daily",
  "weekly",
  "monthly",
  "quarterly",
  "yearly",
];

const REPORT_TYPES = [
  "executive_summary",
  "revenue",
  "customer",
  "ai_usage",
  "business_alerts",
  "full_pack",
] as const;

type CenterPayload = {
  revenue: {
    revenue: {
      mrrUsd: number;
      arrUsd: number;
      ledgerCollectedUsd: number;
      testerOneTimeEstimateUsd: number;
    };
    paid: {
      standardActive: number;
      premiumActive: number;
      testerAccounts: number;
      activeSubscriptions: number;
    };
    supportTickets: {
      feedbackSubmissions: number;
      commercialLeads: number;
      marketingLeads: number;
      total: number;
    };
  };
  customer: {
    registrations: {
      total: number;
      today: number;
      week: number;
      month: number;
      verified: number;
      unverified: number;
    };
    activation: {
      usersWithCompletedVideo: number;
      activationRatePct: number | null;
    };
    retention: { active30dProxy: number; note: string };
    upgrades: {
      standardActive: number;
      premiumActive: number;
      note: string;
    };
    cancellations: { cancelledApprox: number; note: string };
    sessions: { status: "N/A"; note: string };
    projects: number;
    videosCompleted: number;
    credits: { remaining: number; charged: number; usersWithZero: number };
  };
  usage: {
    creditRemaining: number;
    creditCharged: number;
    jobsTotal: number;
    projects: number;
  };
  generation: {
    generationsPerDay: Array<{ date: string; count: number }>;
    avgRenderSeconds: number | null;
    gpuUtilization: "N/A";
    queue: { queued: number; running: number };
    creditsChargedPeriod: number;
    popularProviders: Array<{ provider: string; count: number }>;
    failureRatePct: number | null;
    retryRatePct: number | null;
    totalJobsPeriod: number;
    completed: number;
    failed: number;
    dataGaps: string[];
  };
  infrastructure: ExecutiveKpis["systemHealth"];
  support: {
    feedbackSubmissions: number;
    commercialLeadLogs: number;
    marketingLeads: number;
    total: number;
    note: string;
  };
  enterprise: {
    totalLeads: number;
    qualifiedLeads: number;
    openDeals: number;
    pipelineValueUsd: number;
    demos: number;
    closedWon: number;
    closedLost: number;
    conversionRatePct: number;
    forecastUsd: number;
  };
  marketing: {
    marketingLeads: number;
    commercialLeads: number;
    newsletterSubscribers: number | null;
    note: string;
  };
};

type RevenueReport = {
  period: PeriodKey;
  label: string;
  current: {
    signups: number;
    generations: number;
    creditsCharged: number;
    ledgerRevenueUsd: number;
    paymentFailures: number;
  };
  previous: {
    signups: number;
    generations: number;
    creditsCharged: number;
    ledgerRevenueUsd: number;
    paymentFailures: number;
  };
  deltaPct: {
    signups: number | null;
    generations: number | null;
    creditsCharged: number | null;
    ledgerRevenueUsd: number | null;
  };
  mrrSnapshotUsd: number;
};

function deltaLabel(n: number | null): string {
  if (n === null) return "n/a vs prior";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n}% vs prior`;
}

export function ExecutiveDashboardClient() {
  const { secret, setSecret, stored, unlock, lock } = useAdminSecret();
  const [tab, setTab] = useState<TabId>("overview");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<ExecutiveKpis | null>(null);
  const [center, setCenter] = useState<CenterPayload | null>(null);
  const [alerts, setAlerts] = useState<BusinessAlertsResult | null>(null);
  const [period, setPeriod] = useState<PeriodKey>("monthly");
  const [revenueReport, setRevenueReport] = useState<RevenueReport | null>(
    null
  );

  const headers = useCallback(
    () => ({ "x-rtas-admin-secret": stored }),
    [stored]
  );

  const load = useCallback(async () => {
    if (!stored) return;
    setBusy(true);
    setError(null);
    try {
      const [kpiRes, centerRes, alertsRes, revRes] = await Promise.all([
        fetch("/api/admin/executive", { headers: headers() }),
        fetch("/api/admin/business-analytics", { headers: headers() }),
        fetch("/api/admin/business-alerts?persist=0", { headers: headers() }),
        fetch(`/api/admin/revenue-reports?period=${period}`, {
          headers: headers(),
        }),
      ]);

      const kpiJson = (await kpiRes.json()) as {
        ok?: boolean;
        error?: string;
        kpis?: ExecutiveKpis;
      };
      const centerJson = (await centerRes.json()) as {
        ok?: boolean;
        error?: string;
        analytics?: CenterPayload;
      };
      const alertsJson = (await alertsRes.json()) as BusinessAlertsResult & {
        ok?: boolean;
        error?: string;
      };
      const revJson = (await revRes.json()) as {
        ok?: boolean;
        error?: string;
        report?: RevenueReport;
      };

      if (!kpiRes.ok || !kpiJson.ok) {
        throw new Error(kpiJson.error ?? "Executive KPIs unauthorized.");
      }
      setKpis(kpiJson.kpis ?? null);
      setCenter(centerJson.analytics ?? null);
      setAlerts(
        alertsJson.ok
          ? {
              alerts: alertsJson.alerts,
              triggeredCount: alertsJson.triggeredCount,
              generatedAt: alertsJson.generatedAt,
              integrityNote: alertsJson.integrityNote,
            }
          : null
      );
      setRevenueReport(revJson.report ?? null);
      if (!centerRes.ok || !centerJson.ok) {
        setError(
          centerJson.error ?? "Business analytics partially unavailable."
        );
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load executive BI."
      );
      setKpis(null);
    } finally {
      setBusy(false);
    }
  }, [stored, headers, period]);

  useEffect(() => {
    if (stored) void load();
  }, [stored, load]);

  async function downloadReport(
    type: (typeof REPORT_TYPES)[number],
    format: "csv" | "html"
  ) {
    const res = await fetch(
      `/api/admin/executive-reports?type=${type}&format=${format}&period=${period}`,
      { headers: headers() }
    );
    if (!res.ok) {
      const data = (await res.json().catch(() => ({}))) as { error?: string };
      setError(data.error ?? "Report download failed.");
      return;
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename="([^"]+)"/.exec(cd);
    const filename = match?.[1] ?? `rtas-report.${format}`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AdminPageShell
      title="Executive BI"
      subtitle="Live business intelligence — real aggregates only. Gaps labeled N/A."
      stored={stored}
      secret={secret}
      setSecret={setSecret}
      unlock={unlock}
      lock={lock}
      busy={busy}
      error={error}
      onRefresh={() => void load()}
    >
      <div className="flex flex-wrap gap-2 border-b border-ds-border-subtle pb-3">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={
              tab === t.id
                ? "rounded-md bg-ds-surface-glass px-3 py-1.5 text-sm text-zinc-100"
                : "rounded-md px-3 py-1.5 text-sm text-ds-text-muted hover:text-zinc-100"
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && kpis && (
        <section className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <AdminMetricCard
              label="MRR"
              value={formatUsd(kpis.mrrUsd)}
              hint={`ARR ${formatUsd(kpis.arrUsd)}`}
            />
            <AdminMetricCard
              label="New users (MTD)"
              value={kpis.newUsers}
              hint={`${kpis.growth.newUsersToday} today`}
            />
            <AdminMetricCard
              label="Active users (30d proxy)"
              value={kpis.activeUsersProxy}
              hint="Generation/update proxy — not sessions"
            />
            <AdminMetricCard
              label="Paid users"
              value={kpis.paidUsers}
              hint={`Enterprise leads: ${kpis.enterpriseLeads}`}
            />
            <AdminMetricCard
              label="Generations"
              value={kpis.generationsTotal}
              hint={`${kpis.generationsToday} today`}
            />
            <AdminMetricCard
              label="Credits remaining"
              value={kpis.creditRemaining}
              hint={`${kpis.creditConsumed} charged lifetime`}
            />
            <AdminMetricCard
              label="Growth / conversion"
              value={formatPct(kpis.growth.signupToPaidPct)}
              hint={`Activation ${formatPct(kpis.growth.activationPct)} · Verified ${formatPct(kpis.conversion.verifiedPct)}`}
            />
            <AdminMetricCard
              label="Churn proxy"
              value={formatPct(kpis.churn.churnRatePct)}
              hint={kpis.churn.note}
            />
            <AdminMetricCard
              label="LTV estimate"
              value={formatUsd(kpis.ltv.estimateUsd)}
              hint={kpis.ltv.note}
            />
            <AdminMetricCard
              label="ARPU (paid)"
              value={formatUsd(kpis.arpu.paidUsd)}
              hint={`All users ${formatUsd(kpis.arpu.allUsersUsd)}`}
            />
            <AdminMetricCard
              label="System health"
              value={`${kpis.systemHealth.successRatePct}%`}
              hint={`Queue ${kpis.systemHealth.queueDepth} · GPU ${kpis.systemHealth.gpuUtilization}`}
            />
            <AdminMetricCard
              label="Failed jobs (24h)"
              value={kpis.systemHealth.failedJobs24h}
              hint={`Avg render ${kpis.systemHealth.avgGenerationSeconds ?? "N/A"}s`}
            />
          </div>

          <Card className="p-4">
            <h2 className="text-sm font-medium text-zinc-100">
              Revenue by plan
            </h2>
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              {kpis.revenueByPlan.map((p) => (
                <li
                  key={p.plan}
                  className="flex flex-wrap justify-between gap-2"
                >
                  <span className="capitalize text-zinc-200">{p.plan}</span>
                  <span>
                    {p.activeCount} active · MRR{" "}
                    {formatUsd(p.mrrContributionUsd)}
                  </span>
                  <span className="w-full text-xs">{p.note}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card className="space-y-2 p-4 text-sm text-ds-text-muted">
            <p className="text-zinc-200">{kpis.integrityNote}</p>
            <p className="text-xs uppercase tracking-wide">Known gaps</p>
            <ul className="list-disc space-y-1 pl-5">
              {kpis.dataGaps.map((g) => (
                <li key={g}>{g}</li>
              ))}
            </ul>
          </Card>
        </section>
      )}

      {tab === "revenue" && (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {PERIODS.map((p) => (
              <Button
                key={p}
                variant={period === p ? "primary" : "ghost"}
                onClick={() => setPeriod(p)}
              >
                {p}
              </Button>
            ))}
          </div>
          {center && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <AdminMetricCard
                label="MRR"
                value={formatUsd(center.revenue.revenue.mrrUsd)}
              />
              <AdminMetricCard
                label="ARR"
                value={formatUsd(center.revenue.revenue.arrUsd)}
              />
              <AdminMetricCard
                label="Ledger collected"
                value={formatUsd(center.revenue.revenue.ledgerCollectedUsd)}
                hint="BillingTransaction sums"
              />
              <AdminMetricCard
                label="Tester one-time est."
                value={formatUsd(
                  center.revenue.revenue.testerOneTimeEstimateUsd
                )}
                hint="Excluded from MRR"
              />
            </div>
          )}
          {revenueReport && (
            <Card className="overflow-x-auto p-4">
              <h2 className="text-sm font-medium text-zinc-100">
                Period compare — {revenueReport.label}
              </h2>
              <table className="mt-3 w-full text-left text-sm">
                <thead className="text-ds-text-muted">
                  <tr>
                    <th className="py-2">Metric</th>
                    <th>Current</th>
                    <th>Previous</th>
                    <th>Δ%</th>
                  </tr>
                </thead>
                <tbody className="text-zinc-200">
                  {(
                    [
                      ["Signups", "signups"],
                      ["Generations", "generations"],
                      ["Credits charged", "creditsCharged"],
                      ["Ledger revenue USD", "ledgerRevenueUsd"],
                    ] as const
                  ).map(([label, key]) => (
                    <tr key={key} className="border-t border-ds-border-subtle">
                      <td className="py-2">{label}</td>
                      <td>{revenueReport.current[key]}</td>
                      <td>{revenueReport.previous[key]}</td>
                      <td>{deltaLabel(revenueReport.deltaPct[key])}</td>
                    </tr>
                  ))}
                  <tr className="border-t border-ds-border-subtle">
                    <td className="py-2">Payment failures</td>
                    <td>{revenueReport.current.paymentFailures}</td>
                    <td>{revenueReport.previous.paymentFailures}</td>
                    <td>—</td>
                  </tr>
                </tbody>
              </table>
            </Card>
          )}
        </section>
      )}

      {tab === "customer" && center && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <AdminMetricCard
            label="Registrations"
            value={center.customer.registrations.total}
            hint={`+${center.customer.registrations.today} today`}
          />
          <AdminMetricCard
            label="Verified"
            value={center.customer.registrations.verified}
            hint={`${center.customer.registrations.unverified} unverified`}
          />
          <AdminMetricCard
            label="Activation"
            value={formatPct(center.customer.activation.activationRatePct)}
            hint={`${center.customer.activation.usersWithCompletedVideo} with completed video`}
          />
          <AdminMetricCard
            label="Retention (30d proxy)"
            value={center.customer.retention.active30dProxy}
            hint={center.customer.retention.note}
          />
          <AdminMetricCard
            label="Standard / Premium"
            value={`${center.customer.upgrades.standardActive} / ${center.customer.upgrades.premiumActive}`}
          />
          <AdminMetricCard
            label="Cancellations"
            value={center.customer.cancellations.cancelledApprox}
            hint={center.customer.cancellations.note}
          />
          <AdminMetricCard
            label="Sessions"
            value="N/A"
            hint={center.customer.sessions.note}
          />
          <AdminMetricCard
            label="Projects / videos"
            value={`${center.customer.projects} / ${center.customer.videosCompleted}`}
            hint={`Credits rem ${center.customer.credits.remaining}`}
          />
        </section>
      )}

      {tab === "usage" && center && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <AdminMetricCard
            label="Credits remaining"
            value={center.usage.creditRemaining}
          />
          <AdminMetricCard
            label="Credits charged"
            value={center.usage.creditCharged}
          />
          <AdminMetricCard label="Jobs (30d)" value={center.usage.jobsTotal} />
          <AdminMetricCard label="Projects" value={center.usage.projects} />
        </section>
      )}

      {tab === "generation" && center && (
        <section className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <AdminMetricCard
              label="Jobs (period)"
              value={center.generation.totalJobsPeriod}
              hint={`${center.generation.completed} ok / ${center.generation.failed} fail`}
            />
            <AdminMetricCard
              label="Avg render"
              value={
                center.generation.avgRenderSeconds !== null
                  ? `${center.generation.avgRenderSeconds}s`
                  : "N/A"
              }
            />
            <AdminMetricCard
              label="GPU util"
              value="N/A"
              hint="Not instrumented"
            />
            <AdminMetricCard
              label="Queue"
              value={`${center.generation.queue.queued} / ${center.generation.queue.running}`}
              hint="queued / running"
            />
            <AdminMetricCard
              label="Failure rate"
              value={formatPct(center.generation.failureRatePct)}
            />
            <AdminMetricCard
              label="Retry rate"
              value={formatPct(center.generation.retryRatePct)}
            />
            <AdminMetricCard
              label="Credits charged"
              value={center.generation.creditsChargedPeriod}
            />
          </div>
          <Card className="p-4">
            <h2 className="text-sm font-medium text-zinc-100">
              Popular providers (proxy for models/templates)
            </h2>
            <ul className="mt-3 space-y-1 text-sm text-ds-text-muted">
              {center.generation.popularProviders.length === 0 ? (
                <li>No generation jobs in period (0).</li>
              ) : (
                center.generation.popularProviders.map((p) => (
                  <li key={p.provider}>
                    {p.provider}: {p.count}
                  </li>
                ))
              )}
            </ul>
            <p className="mt-3 text-xs text-ds-text-muted">
              Daily series:{" "}
              {center.generation.generationsPerDay
                .slice(-7)
                .map((d) => `${d.date}:${d.count}`)
                .join(" · ") || "empty"}
            </p>
          </Card>
        </section>
      )}

      {tab === "infrastructure" && center && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <AdminMetricCard
            label="Database"
            value={center.infrastructure.database ? "OK" : "Down"}
          />
          <AdminMetricCard
            label="Queue depth"
            value={center.infrastructure.queueDepth}
          />
          <AdminMetricCard
            label="Running jobs"
            value={center.infrastructure.runningJobs}
          />
          <AdminMetricCard
            label="Success rate"
            value={`${center.infrastructure.successRatePct}%`}
          />
          <AdminMetricCard
            label="Failed (24h)"
            value={center.infrastructure.failedJobs24h}
          />
          <AdminMetricCard label="GPU util" value="N/A" />
        </section>
      )}

      {tab === "support" && center && (
        <section className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <AdminMetricCard
              label="Feedback"
              value={center.support.feedbackSubmissions}
            />
            <AdminMetricCard
              label="Commercial leads (logs)"
              value={center.support.commercialLeadLogs}
            />
            <AdminMetricCard
              label="Marketing leads"
              value={center.support.marketingLeads}
            />
            <AdminMetricCard
              label="Total signals"
              value={center.support.total}
            />
          </div>
          <p className="text-sm text-ds-text-muted">{center.support.note}</p>
        </section>
      )}

      {tab === "enterprise" && center && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <AdminMetricCard
            label="Total leads"
            value={center.enterprise.totalLeads}
          />
          <AdminMetricCard
            label="Qualified"
            value={center.enterprise.qualifiedLeads}
          />
          <AdminMetricCard
            label="Open deals"
            value={center.enterprise.openDeals}
          />
          <AdminMetricCard
            label="Pipeline value"
            value={formatUsd(center.enterprise.pipelineValueUsd)}
            hint="Only leads with estimatedValueUsd set"
          />
          <AdminMetricCard label="Demos" value={center.enterprise.demos} />
          <AdminMetricCard
            label="Closed won / lost"
            value={`${center.enterprise.closedWon} / ${center.enterprise.closedLost}`}
          />
          <AdminMetricCard
            label="Conversion %"
            value={`${center.enterprise.conversionRatePct}%`}
          />
          <AdminMetricCard
            label="Forecast USD"
            value={formatUsd(center.enterprise.forecastUsd)}
          />
        </section>
      )}

      {tab === "marketing" && center && (
        <section className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <AdminMetricCard
              label="Marketing leads"
              value={center.marketing.marketingLeads}
            />
            <AdminMetricCard
              label="Commercial lead logs"
              value={center.marketing.commercialLeads}
            />
            <AdminMetricCard
              label="Newsletter"
              value={
                center.marketing.newsletterSubscribers === null
                  ? "N/A"
                  : center.marketing.newsletterSubscribers
              }
            />
          </div>
          <p className="text-sm text-ds-text-muted">{center.marketing.note}</p>
        </section>
      )}

      {tab === "reports" && (
        <section className="space-y-4">
          <p className="text-sm text-ds-text-muted">
            CSV is required. Printable HTML is available for browser Print → PDF
            (no heavy PDF dependency).
          </p>
          <div className="flex flex-wrap gap-2">
            {PERIODS.map((p) => (
              <Button
                key={p}
                variant={period === p ? "primary" : "ghost"}
                onClick={() => setPeriod(p)}
              >
                {p}
              </Button>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {REPORT_TYPES.map((type) => (
              <Card
                key={type}
                className="flex flex-wrap items-center gap-2 p-4"
              >
                <span className="flex-1 text-sm text-zinc-100">{type}</span>
                <Button
                  variant="primary"
                  onClick={() => void downloadReport(type, "csv")}
                >
                  CSV
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => void downloadReport(type, "html")}
                >
                  HTML
                </Button>
              </Card>
            ))}
          </div>
        </section>
      )}

      {tab === "alerts" && alerts && (
        <section className="space-y-4">
          <AdminMetricCard
            label="Triggered now"
            value={alerts.triggeredCount}
            hint={alerts.integrityNote}
          />
          <ul className="space-y-3">
            {alerts.alerts.map((a) => (
              <Card
                key={a.id}
                className={`p-4 ${a.triggered ? "border border-amber-500/40" : ""}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-zinc-100">{a.title}</p>
                  <span className="text-xs uppercase text-ds-text-muted">
                    {a.severity}
                    {a.triggered ? " · TRIGGERED" : " · ok"}
                  </span>
                </div>
                <p className="mt-1 text-sm text-ds-text-muted">{a.message}</p>
                <p className="mt-1 text-xs text-ds-text-muted">
                  {a.category} · threshold {a.threshold} · value{" "}
                  {String(a.metricValue ?? "—")}
                </p>
              </Card>
            ))}
          </ul>
        </section>
      )}
    </AdminPageShell>
  );
}
