/**
 * Phase 13 Sprint 7 — Executive report builders (CSV + printable HTML).
 * No heavy Excel/PDF deps — CSV required; HTML printable documented as PDF path.
 */

import {
  fetchAiUsageAnalytics,
  fetchBusinessAnalyticsCenter,
  fetchCustomerAnalytics,
  fetchExecutiveKpis,
  fetchRevenuePeriodReport,
  type PeriodKey,
} from "@/lib/server/admin/executive-bi";
import { evaluateBusinessAlerts } from "@/lib/server/admin/business-alerts";

export const EXECUTIVE_REPORT_TYPES = [
  "executive_summary",
  "revenue",
  "customer",
  "ai_usage",
  "business_alerts",
  "full_pack",
] as const;

export type ExecutiveReportType = (typeof EXECUTIVE_REPORT_TYPES)[number];

function csvEscape(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function toCsv(headers: string[], rows: Array<Array<string | number | null | undefined>>): string {
  const lines = [
    headers.map(csvEscape).join(","),
    ...rows.map((r) => r.map(csvEscape).join(",")),
  ];
  return lines.join("\n");
}

export type BuiltReport = {
  filename: string;
  contentType: string;
  body: string;
  format: "csv" | "html";
};

export async function buildExecutiveReport(options: {
  type: ExecutiveReportType;
  format?: "csv" | "html";
  period?: PeriodKey;
}): Promise<BuiltReport> {
  const format = options.format ?? "csv";
  const period = options.period ?? "monthly";
  const stamp = new Date().toISOString().slice(0, 10);

  if (format === "html") {
    const html = await buildPrintableHtml(options.type, period);
    return {
      filename: `rtas-${options.type}-${stamp}.html`,
      contentType: "text/html; charset=utf-8",
      body: html,
      format: "html",
    };
  }

  switch (options.type) {
    case "executive_summary": {
      const k = await fetchExecutiveKpis();
      const body = toCsv(
        ["metric", "value", "note"],
        [
          ["mrr_usd", k.mrrUsd, "list-price × active Standard/Premium"],
          ["arr_usd", k.arrUsd, "MRR × 12"],
          ["new_users_mtd", k.newUsers, ""],
          ["active_users_30d_proxy", k.activeUsersProxy, k.dataGaps[1] ?? ""],
          ["paid_users", k.paidUsers, ""],
          ["enterprise_leads", k.enterpriseLeads, ""],
          ["generations_total", k.generationsTotal, ""],
          ["generations_today", k.generationsToday, ""],
          ["credits_remaining", k.creditRemaining, ""],
          ["credits_consumed", k.creditConsumed, ""],
          ["signup_to_paid_pct", k.growth.signupToPaidPct, ""],
          ["activation_pct", k.growth.activationPct, ""],
          ["churn_rate_pct", k.churn.churnRatePct, k.churn.note],
          ["ltv_estimate_usd", k.ltv.estimateUsd, k.ltv.note],
          ["arpu_paid_usd", k.arpu.paidUsd, ""],
          ["queue_depth", k.systemHealth.queueDepth, ""],
          ["success_rate_pct", k.systemHealth.successRatePct, ""],
          ["gpu_utilization", "N/A", "not instrumented"],
          ["generated_at", k.generatedAt, k.integrityNote],
        ]
      );
      return {
        filename: `rtas-executive-summary-${stamp}.csv`,
        contentType: "text/csv; charset=utf-8",
        body,
        format: "csv",
      };
    }
    case "revenue": {
      const r = await fetchRevenuePeriodReport(period);
      const body = toCsv(
        ["field", "current", "previous", "delta_pct"],
        [
          ["period", r.period, r.label, ""],
          ["signups", r.current.signups, r.previous.signups, r.deltaPct.signups],
          [
            "generations",
            r.current.generations,
            r.previous.generations,
            r.deltaPct.generations,
          ],
          [
            "credits_charged",
            r.current.creditsCharged,
            r.previous.creditsCharged,
            r.deltaPct.creditsCharged,
          ],
          [
            "ledger_revenue_usd",
            r.current.ledgerRevenueUsd,
            r.previous.ledgerRevenueUsd,
            r.deltaPct.ledgerRevenueUsd,
          ],
          [
            "payment_failures",
            r.current.paymentFailures,
            r.previous.paymentFailures,
            "",
          ],
          ["mrr_snapshot_usd", r.mrrSnapshotUsd, "", ""],
        ]
      );
      return {
        filename: `rtas-revenue-${period}-${stamp}.csv`,
        contentType: "text/csv; charset=utf-8",
        body,
        format: "csv",
      };
    }
    case "customer": {
      const c = await fetchCustomerAnalytics();
      const body = toCsv(
        ["metric", "value", "note"],
        [
          ["registrations_total", c.registrations.total, ""],
          ["registrations_today", c.registrations.today, ""],
          ["registrations_week", c.registrations.week, ""],
          ["registrations_month", c.registrations.month, ""],
          ["verified", c.registrations.verified, ""],
          ["unverified", c.registrations.unverified, ""],
          ["activated_with_video", c.activation.usersWithCompletedVideo, ""],
          ["activation_rate_pct", c.activation.activationRatePct, ""],
          ["active_30d_proxy", c.retention.active30dProxy, c.retention.note],
          ["standard_active", c.upgrades.standardActive, ""],
          ["premium_active", c.upgrades.premiumActive, ""],
          ["cancellations_approx", c.cancellations.cancelledApprox, c.cancellations.note],
          ["sessions", "N/A", c.sessions.note],
          ["projects", c.projects, ""],
          ["videos_completed", c.videosCompleted, ""],
          ["credits_remaining", c.credits.remaining, ""],
          ["credits_charged", c.credits.charged, ""],
        ]
      );
      return {
        filename: `rtas-customer-${stamp}.csv`,
        contentType: "text/csv; charset=utf-8",
        body,
        format: "csv",
      };
    }
    case "ai_usage": {
      const a = await fetchAiUsageAnalytics(30);
      const rows: Array<Array<string | number | null>> = [
        ["period_days", a.periodDays, ""],
        ["total_jobs", a.totalJobsPeriod, ""],
        ["completed", a.completed, ""],
        ["failed", a.failed, ""],
        ["failure_rate_pct", a.failureRatePct, ""],
        ["retry_jobs", a.retryJobs, ""],
        ["retry_rate_pct", a.retryRatePct, ""],
        ["avg_render_seconds", a.avgRenderSeconds, ""],
        ["gpu_utilization", "N/A", ""],
        ["queued", a.queue.queued, ""],
        ["running", a.queue.running, ""],
        ["credits_charged", a.creditsChargedPeriod, ""],
      ];
      for (const p of a.popularProviders) {
        rows.push([`provider:${p.provider}`, p.count, ""]);
      }
      for (const d of a.generationsPerDay) {
        rows.push([`day:${d.date}`, d.count, ""]);
      }
      const body = toCsv(["metric", "value", "note"], rows);
      return {
        filename: `rtas-ai-usage-${stamp}.csv`,
        contentType: "text/csv; charset=utf-8",
        body,
        format: "csv",
      };
    }
    case "business_alerts": {
      const alerts = await evaluateBusinessAlerts({ persist: false });
      const body = toCsv(
        ["id", "category", "severity", "triggered", "title", "metric", "threshold", "message"],
        alerts.alerts.map((a) => [
          a.id,
          a.category,
          a.severity,
          a.triggered ? "yes" : "no",
          a.title,
          a.metricValue,
          a.threshold,
          a.message,
        ])
      );
      return {
        filename: `rtas-business-alerts-${stamp}.csv`,
        contentType: "text/csv; charset=utf-8",
        body,
        format: "csv",
      };
    }
    case "full_pack": {
      const [k, c, a, r, alerts] = await Promise.all([
        fetchExecutiveKpis(),
        fetchCustomerAnalytics(),
        fetchAiUsageAnalytics(30),
        fetchRevenuePeriodReport(period),
        evaluateBusinessAlerts({ persist: false }),
      ]);
      const body = toCsv(
        ["section", "metric", "value"],
        [
          ["executive", "mrr_usd", k.mrrUsd],
          ["executive", "arr_usd", k.arrUsd],
          ["executive", "paid_users", k.paidUsers],
          ["executive", "enterprise_leads", k.enterpriseLeads],
          ["customer", "registrations_total", c.registrations.total],
          ["customer", "activation_rate_pct", c.activation.activationRatePct],
          ["ai_usage", "jobs_period", a.totalJobsPeriod],
          ["ai_usage", "failure_rate_pct", a.failureRatePct],
          ["revenue", `ledger_${period}`, r.current.ledgerRevenueUsd],
          ["alerts", "triggered_count", alerts.triggeredCount],
        ]
      );
      return {
        filename: `rtas-full-pack-${stamp}.csv`,
        contentType: "text/csv; charset=utf-8",
        body,
        format: "csv",
      };
    }
  }
}

async function buildPrintableHtml(
  type: ExecutiveReportType,
  period: PeriodKey
): Promise<string> {
  const center = await fetchBusinessAnalyticsCenter();
  const kpis = await fetchExecutiveKpis();
  const revenue = await fetchRevenuePeriodReport(period);
  const alerts = await evaluateBusinessAlerts({ persist: false });

  const rows = [
    ["Report type", type],
    ["Generated", new Date().toISOString()],
    ["MRR (USD)", String(kpis.mrrUsd)],
    ["ARR (USD)", String(kpis.arrUsd)],
    ["Paid users", String(kpis.paidUsers)],
    ["Enterprise leads", String(kpis.enterpriseLeads)],
    ["Generations today", String(kpis.generationsToday)],
    ["Credits remaining", String(kpis.creditRemaining)],
    [`Ledger revenue (${period})`, String(revenue.current.ledgerRevenueUsd)],
    ["Triggered alerts", String(alerts.triggeredCount)],
    ["Support signals", String(center.support.total)],
    ["GPU utilization", "N/A"],
    ["Integrity", kpis.integrityNote],
  ];

  const tr = rows
    .map(
      ([k, v]) =>
        `<tr><th style="text-align:left;padding:6px;border-bottom:1px solid #333">${escapeHtml(
          k
        )}</th><td style="padding:6px;border-bottom:1px solid #333">${escapeHtml(
          v
        )}</td></tr>`
    )
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>RTAS Studio AI — Executive Report</title>
  <style>
    body { font-family: Georgia, serif; background: #0a0a0a; color: #f4f4f5; padding: 32px; }
    h1 { font-size: 22px; margin: 0 0 8px; }
    p { color: #a1a1aa; font-size: 13px; }
    table { width: 100%; border-collapse: collapse; margin-top: 24px; }
    @media print { body { background: #fff; color: #111; } p { color: #444; } }
  </style>
</head>
<body>
  <h1>RTAS Studio AI — Executive Report</h1>
  <p>Printable HTML (use browser Print → Save as PDF). CSV is the primary machine-readable export. No fabricated metrics.</p>
  <table>${tr}</table>
</body>
</html>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
