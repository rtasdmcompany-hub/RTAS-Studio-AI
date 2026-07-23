/**
 * Phase 13 Sprint 7 — Rule-based business alerts for admin BI.
 * Evaluates live DB signals; persists high-severity hits to SystemLog.
 */

import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { logSystemEvent } from "@/lib/server/audit-log";
import { fetchAdminDashboardMetrics } from "@/lib/server/admin/metrics";
import { getEnterpriseDashboardMetrics } from "@/lib/enterprise/crm";

const MS_DAY = 24 * 60 * 60 * 1000;

export type BusinessAlertSeverity = "info" | "warn" | "critical";

export type BusinessAlert = {
  id: string;
  category:
    | "payments"
    | "errors"
    | "credits"
    | "gpu_queue"
    | "infrastructure"
    | "security"
    | "enterprise"
    | "downtime";
  severity: BusinessAlertSeverity;
  title: string;
  message: string;
  metricValue: number | string | null;
  threshold: string;
  triggered: boolean;
  evaluatedAt: string;
};

export type BusinessAlertsResult = {
  alerts: BusinessAlert[];
  triggeredCount: number;
  generatedAt: string;
  integrityNote: string;
};

/**
 * Evaluate rule-based alerts. Does not invent incidents — only fires when
 * measured values cross thresholds.
 */
export async function evaluateBusinessAlerts(options?: {
  persist?: boolean;
}): Promise<BusinessAlertsResult> {
  const now = new Date();
  const evaluatedAt = now.toISOString();
  const dayAgo = new Date(now.getTime() - MS_DAY);

  if (!isPrismaConfigured()) {
    return {
      alerts: [
        {
          id: "infra.db_unconfigured",
          category: "infrastructure",
          severity: "critical",
          title: "Database not configured",
          message: "Prisma / DATABASE_URL unavailable — BI and alerts cannot run.",
          metricValue: null,
          threshold: "DATABASE_URL required",
          triggered: true,
          evaluatedAt,
        },
      ],
      triggeredCount: 1,
      generatedAt: evaluatedAt,
      integrityNote: "Only real configuration and DB signals are evaluated.",
    };
  }

  const [
    ops,
    enterprise,
    paymentFailures24h,
    errorLogs24h,
    securityWarns24h,
    maintenanceActive,
    failedJobs24h,
    largeLeads,
  ] = await Promise.all([
    fetchAdminDashboardMetrics(),
    getEnterpriseDashboardMetrics(),
    prisma.billingTransaction.count({
      where: {
        createdAt: { gte: dayAgo },
        OR: [
          { status: { in: ["failed", "error", "declined"] } },
          { eventType: { contains: "fail" } },
          { eventType: { contains: "payment_failed" } },
        ],
      },
    }),
    prisma.systemLog.count({
      where: { level: "error", createdAt: { gte: dayAgo } },
    }),
    prisma.systemLog.count({
      where: {
        createdAt: { gte: dayAgo },
        OR: [
          { source: { contains: "security" } },
          { source: { contains: "auth" }, level: { in: ["warn", "error"] } },
        ],
      },
    }),
    prisma.maintenanceEvent.count({
      where: { status: { in: ["active", "in_progress", "ongoing"] } },
    }),
    prisma.generationJob.count({
      where: { status: "FAILED", createdAt: { gte: dayAgo } },
    }),
    prisma.enterpriseLead.count({
      where: {
        OR: [
          { estimatedValueUsd: { gte: 5000 } },
            { priority: { in: ["high", "urgent"] } },
        ],
        stage: { notIn: ["closed_won", "closed_lost"] },
      },
    }),
  ]);

  const queueDepth = ops.jobs.queued + ops.jobs.running;
  const creditRemaining = ops.credits.totalRemaining;
  const successRate = ops.jobs.successRate;

  const candidates: Omit<BusinessAlert, "evaluatedAt">[] = [
    {
      id: "payments.failures_24h",
      category: "payments",
      severity: paymentFailures24h >= 5 ? "critical" : "warn",
      title: "Payment failures (24h)",
      message: `${paymentFailures24h} billing transaction(s) marked failed/declined in the last 24 hours.`,
      metricValue: paymentFailures24h,
      threshold: "warn ≥ 1 · critical ≥ 5",
      triggered: paymentFailures24h >= 1,
    },
    {
      id: "errors.system_logs_24h",
      category: "errors",
      severity: errorLogs24h >= 25 ? "critical" : "warn",
      title: "Elevated error logs (24h)",
      message: `${errorLogs24h} SystemLog error-level rows in the last 24 hours.`,
      metricValue: errorLogs24h,
      threshold: "warn ≥ 10 · critical ≥ 25",
      triggered: errorLogs24h >= 10,
    },
    {
      id: "errors.job_failures_24h",
      category: "errors",
      severity: failedJobs24h >= 20 ? "critical" : "warn",
      title: "Generation failures (24h)",
      message: `${failedJobs24h} FAILED generation jobs in the last 24 hours (success rate ${successRate}%).`,
      metricValue: failedJobs24h,
      threshold: "warn ≥ 5 · critical ≥ 20",
      triggered: failedJobs24h >= 5,
    },
    {
      id: "credits.low_inventory",
      category: "credits",
      severity: creditRemaining <= 0 ? "critical" : "warn",
      title: "Low platform credit inventory",
      message: `Sum of User.credits remaining is ${creditRemaining}.`,
      metricValue: creditRemaining,
      threshold: "warn ≤ 500 · critical ≤ 0 (aggregate)",
      triggered: creditRemaining <= 500,
    },
    {
      id: "gpu_queue.depth",
      category: "gpu_queue",
      severity: queueDepth >= 50 ? "critical" : "warn",
      title: "GPU / generation queue depth",
      message: `${ops.jobs.queued} queued + ${ops.jobs.running} running = ${queueDepth}.`,
      metricValue: queueDepth,
      threshold: "warn ≥ 15 · critical ≥ 50",
      triggered: queueDepth >= 15,
    },
    {
      id: "infrastructure.maintenance",
      category: "infrastructure",
      severity: "warn",
      title: "Active maintenance window",
      message: `${maintenanceActive} MaintenanceEvent row(s) marked active/in_progress.`,
      metricValue: maintenanceActive,
      threshold: "any active maintenance",
      triggered: maintenanceActive >= 1,
    },
    {
      id: "infrastructure.db_ok",
      category: "infrastructure",
      severity: "info",
      title: "Database reachable",
      message: "Prisma queries succeeded for alert evaluation.",
      metricValue: 1,
      threshold: "connectivity check",
      triggered: false,
    },
    {
      id: "security.warn_events_24h",
      category: "security",
      severity: securityWarns24h >= 50 ? "critical" : "warn",
      title: "Security / auth warning volume",
      message: `${securityWarns24h} security/auth warn+error SystemLog rows in 24h.`,
      metricValue: securityWarns24h,
      threshold: "warn ≥ 20 · critical ≥ 50",
      triggered: securityWarns24h >= 20,
    },
    {
      id: "enterprise.large_lead",
      category: "enterprise",
      severity: "info",
      title: "Large / high-priority enterprise lead",
      message: `${largeLeads} open enterprise lead(s) with estimatedValue ≥ $5k or high/urgent priority.`,
      metricValue: largeLeads,
      threshold: "any matching open lead",
      triggered: largeLeads >= 1,
    },
    {
      id: "downtime.success_rate",
      category: "downtime",
      severity: successRate < 70 ? "critical" : "warn",
      title: "Generation success rate pressure",
      message: `Lifetime finished-job success rate is ${successRate}%.`,
      metricValue: successRate,
      threshold: "warn < 90% · critical < 70% (when finished jobs exist)",
      triggered:
        ops.jobs.completed + ops.jobs.failed > 0 && successRate < 90,
    },
  ];

  // Soft info: enterprise pipeline empty is not an alert — only positive signals above.
  void enterprise;

  const alerts: BusinessAlert[] = candidates.map((c) => ({
    ...c,
    evaluatedAt,
  }));

  const triggered = alerts.filter((a) => a.triggered);

  if (options?.persist !== false) {
    for (const alert of triggered.filter(
      (a) => a.severity === "critical" || a.severity === "warn"
    )) {
      await logSystemEvent({
        level: alert.severity === "critical" ? "error" : "warn",
        source: `business.alert.${alert.category}`,
        message: `[${alert.severity}] ${alert.title}: ${alert.message}`,
        metadata: {
          alertId: alert.id,
          metricValue: alert.metricValue,
          threshold: alert.threshold,
        },
      });
    }
  }

  return {
    alerts,
    triggeredCount: triggered.length,
    generatedAt: evaluatedAt,
    integrityNote:
      "Rule-based only. Triggered alerts reflect measured DB/log thresholds. No fabricated incidents.",
  };
}
