"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Alert, Button, Card } from "@rtas/ui";
import {
  ENTERPRISE_PIPELINE_STAGES,
  ENTERPRISE_PRIORITIES,
  ENTERPRISE_STAGE_LABELS,
  ENTERPRISE_LEAD_STATUSES,
  type EnterprisePipelineStage,
} from "@/lib/enterprise/pipeline";
import type { EnterpriseDashboardMetrics } from "@/lib/enterprise/crm";

const ADMIN_KEY = "rtas_admin_secret";

type LeadActivity = {
  id: string;
  type: string;
  body: string;
  actor: string;
  createdAt: string;
};

type Lead = {
  id: string;
  name: string;
  email: string;
  company: string | null;
  role: string | null;
  stage: string;
  status: string;
  priority: string;
  owner: string | null;
  tags: string;
  notes: string | null;
  estimatedValueUsd: number | null;
  requestType: string | null;
  demoType: string | null;
  planInterest: string | null;
  createdAt: string;
  activities?: LeadActivity[];
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

const fieldClass =
  "w-full rounded-md border border-ds-border-subtle bg-ds-surface-glass px-3 py-2 text-sm text-zinc-100";

export function AdminEnterpriseClient() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<
    (EnterpriseDashboardMetrics & { dbConfigured?: boolean }) | null
  >(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [stage, setStage] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [note, setNote] = useState("");

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
  }, []);

  const selected = useMemo(
    () => leads.find((l) => l.id === selectedId) || null,
    [leads, selectedId]
  );

  const load = useCallback(
    async (adminSecret: string) => {
      setBusy(true);
      setError(null);
      try {
        const headers = { "x-rtas-admin-secret": adminSecret };
        const params = new URLSearchParams();
        if (q.trim()) params.set("q", q.trim());
        if (stage) params.set("stage", stage);
        if (status) params.set("status", status);
        if (priority) params.set("priority", priority);

        const [metricsRes, leadsRes] = await Promise.all([
          fetch("/api/admin/enterprise?view=metrics", { headers }),
          fetch(`/api/admin/enterprise?${params.toString()}`, { headers }),
        ]);
        const metricsJson = (await metricsRes.json()) as {
          ok?: boolean;
          error?: string;
          metrics?: EnterpriseDashboardMetrics & { dbConfigured?: boolean };
        };
        const leadsJson = (await leadsRes.json()) as {
          ok?: boolean;
          error?: string;
          leads?: Lead[];
          total?: number;
          dbConfigured?: boolean;
        };

        if (!metricsRes.ok || !metricsJson.ok) {
          throw new Error(metricsJson.error ?? "Unauthorized or unavailable.");
        }
        if (!leadsRes.ok || !leadsJson.ok) {
          throw new Error(leadsJson.error ?? "Could not load leads.");
        }

        setMetrics(metricsJson.metrics ?? null);
        setLeads(leadsJson.leads ?? []);
        setTotal(leadsJson.total ?? 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load enterprise CRM.");
        setMetrics(null);
        setLeads([]);
        setTotal(0);
      } finally {
        setBusy(false);
      }
    },
    [q, stage, status, priority]
  );

  useEffect(() => {
    if (stored) void load(stored);
  }, [stored, load]);

  function unlock(e: React.FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;
    sessionStorage.setItem(ADMIN_KEY, secret.trim());
    setStored(secret.trim());
  }

  async function patchLead(patch: Record<string, unknown>) {
    if (!stored || !selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/enterprise", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "x-rtas-admin-secret": stored,
        },
        body: JSON.stringify({ id: selectedId, ...patch }),
      });
      const data = (await res.json()) as { ok?: boolean; error?: string; lead?: Lead };
      if (!res.ok || !data.ok) throw new Error(data.error || "Update failed.");
      setLeads((prev) => prev.map((l) => (l.id === data.lead!.id ? { ...l, ...data.lead! } : l)));
      await load(stored);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!stored) {
    return (
      <div className="mx-auto max-w-md p-6">
        <h1 className="text-xl text-zinc-100">Enterprise CRM</h1>
        <p className="mt-2 text-sm text-ds-text-muted">
          Enter your RTAS admin secret to view live pipeline data (zeros until real leads arrive).
        </p>
        <form className="mt-6 space-y-3" onSubmit={unlock}>
          <input
            type="password"
            className={fieldClass}
            placeholder="RTAS_ADMIN_SECRET"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
          />
          <Button type="submit" variant="primary" className="w-full">
            Unlock enterprise CRM
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Enterprise sales CRM</h1>
          <p className="text-sm text-ds-text-muted">
            Live counts only — empty pipeline shows zeros, never fabricated metrics.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/admin" className="rtas-btn-ghost rtas-ui-btn">
            Ops dashboard
          </Link>
          <Link href="/admin/enterprise/proposals" className="rtas-btn-ghost rtas-ui-btn">
            Proposals
          </Link>
          <Button variant="ghost" disabled={busy} onClick={() => void load(stored)}>
            Refresh
          </Button>
        </div>
      </div>

      {error ? <Alert variant="error" message={error} /> : null}

      {metrics ? (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Total leads" value={metrics.totalLeads} />
          <MetricCard label="Qualified" value={metrics.qualifiedLeads} />
          <MetricCard label="Open deals" value={metrics.openDeals} />
          <MetricCard
            label="Pipeline value"
            value={`$${metrics.pipelineValueUsd}`}
            hint="Sum of estimated values on open stages only"
          />
          <MetricCard label="Demos" value={metrics.demos} />
          <MetricCard
            label="Conversion"
            value={`${metrics.conversionRatePct}%`}
            hint={`Won ${metrics.closedWon} / Lost ${metrics.closedLost}`}
          />
          <MetricCard
            label="Forecast"
            value={`$${metrics.forecastUsd}`}
            hint="Equals open pipeline value (no invented multipliers)"
          />
          <MetricCard
            label="DB"
            value={metrics.dbConfigured ? "Connected" : "Offline"}
            hint={metrics.dbConfigured ? undefined : "Configure DATABASE_URL"}
          />
        </section>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(metrics?.byStage || []).map((row) => (
          <Card key={row.stage} className="p-3">
            <p className="text-xs text-ds-text-muted">
              {ENTERPRISE_STAGE_LABELS[row.stage as EnterprisePipelineStage] || row.stage}
            </p>
            <p className="text-lg text-zinc-100">{row.count}</p>
          </Card>
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg text-zinc-100">Pipeline</h2>
        <div className="grid gap-3 md:grid-cols-4">
          <input
            className={fieldClass}
            placeholder="Search name, email, company…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Search leads"
          />
          <select
            className={fieldClass}
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            aria-label="Filter by stage"
          >
            <option value="">All stages</option>
            {ENTERPRISE_PIPELINE_STAGES.map((s) => (
              <option key={s} value={s}>
                {ENTERPRISE_STAGE_LABELS[s]}
              </option>
            ))}
          </select>
          <select
            className={fieldClass}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            {ENTERPRISE_LEAD_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            className={fieldClass}
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            aria-label="Filter by priority"
          >
            <option value="">All priorities</option>
            {ENTERPRISE_PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <Button variant="primary" disabled={busy} onClick={() => void load(stored)}>
          Apply filters
        </Button>
        <p className="text-sm text-ds-text-muted">
          {total === 0
            ? "No leads yet — empty state is intentional until real inquiries arrive."
            : `${total} lead${total === 1 ? "" : "s"}`}
        </p>

        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/[0.04] text-ds-text-muted">
              <tr>
                <th className="px-3 py-2 font-medium">Company</th>
                <th className="px-3 py-2 font-medium">Contact</th>
                <th className="px-3 py-2 font-medium">Stage</th>
                <th className="px-3 py-2 font-medium">Priority</th>
                <th className="px-3 py-2 font-medium">Owner</th>
                <th className="px-3 py-2 font-medium">Value</th>
              </tr>
            </thead>
            <tbody>
              {leads.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-ds-text-muted">
                    Empty pipeline. Submit a real inquiry from /enterprise or /demo to populate.
                  </td>
                </tr>
              ) : (
                leads.map((lead) => (
                  <tr
                    key={lead.id}
                    className={`cursor-pointer border-t border-white/5 hover:bg-white/[0.03] ${
                      selectedId === lead.id ? "bg-white/[0.05]" : ""
                    }`}
                    onClick={() => setSelectedId(lead.id)}
                  >
                    <td className="px-3 py-2 text-zinc-100">{lead.company || "—"}</td>
                    <td className="px-3 py-2">
                      <div className="text-zinc-100">{lead.name}</div>
                      <div className="text-xs text-ds-text-muted">{lead.email}</div>
                    </td>
                    <td className="px-3 py-2 text-ds-text-muted">
                      {ENTERPRISE_STAGE_LABELS[lead.stage as EnterprisePipelineStage] ||
                        lead.stage}
                    </td>
                    <td className="px-3 py-2 text-ds-text-muted">{lead.priority}</td>
                    <td className="px-3 py-2 text-ds-text-muted">{lead.owner || "—"}</td>
                    <td className="px-3 py-2 text-ds-text-muted">
                      {typeof lead.estimatedValueUsd === "number"
                        ? `$${lead.estimatedValueUsd}`
                        : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {selected ? (
        <section className="space-y-4 rounded-2xl border border-white/10 p-4">
          <h2 className="text-lg text-zinc-100">
            {selected.company || selected.name} — deal detail
          </h2>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="text-sm text-ds-text-muted">
              Stage
              <select
                className={`${fieldClass} mt-1`}
                value={selected.stage}
                onChange={(e) => void patchLead({ stage: e.target.value })}
              >
                {ENTERPRISE_PIPELINE_STAGES.map((s) => (
                  <option key={s} value={s}>
                    {ENTERPRISE_STAGE_LABELS[s]}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm text-ds-text-muted">
              Priority
              <select
                className={`${fieldClass} mt-1`}
                value={selected.priority}
                onChange={(e) => void patchLead({ priority: e.target.value })}
              >
                {ENTERPRISE_PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm text-ds-text-muted">
              Owner
              <input
                className={`${fieldClass} mt-1`}
                defaultValue={selected.owner || ""}
                onBlur={(e) => void patchLead({ owner: e.target.value || null })}
                placeholder="Owner name"
              />
            </label>
            <label className="text-sm text-ds-text-muted">
              Est. value (USD)
              <input
                type="number"
                min={0}
                className={`${fieldClass} mt-1`}
                defaultValue={selected.estimatedValueUsd ?? ""}
                onBlur={(e) => {
                  const v = e.target.value.trim();
                  void patchLead({
                    estimatedValueUsd: v === "" ? null : Number(v),
                  });
                }}
                placeholder="Leave blank — never invent"
              />
            </label>
          </div>
          <label className="block text-sm text-ds-text-muted">
            Tags (comma-separated)
            <input
              className={`${fieldClass} mt-1`}
              defaultValue={selected.tags || ""}
              onBlur={(e) => void patchLead({ tags: e.target.value })}
            />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <h3 className="text-sm text-zinc-100">Add note</h3>
              <textarea
                className={`${fieldClass} mt-1 min-h-[100px]`}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Next step, call notes…"
              />
              <Button
                className="mt-2"
                variant="primary"
                disabled={busy || !note.trim()}
                onClick={() => {
                  void patchLead({ note: note.trim() }).then(() => setNote(""));
                }}
              >
                Save note
              </Button>
            </div>
            <div>
              <h3 className="text-sm text-zinc-100">Activity timeline</h3>
              <ul className="mt-2 max-h-56 space-y-2 overflow-y-auto text-sm">
                {(selected.activities || []).length === 0 ? (
                  <li className="text-ds-text-muted">No activity yet.</li>
                ) : (
                  (selected.activities || []).map((a) => (
                    <li key={a.id} className="rounded-md border border-white/5 p-2">
                      <p className="text-xs text-ds-text-muted">
                        {a.type} · {a.actor} · {new Date(a.createdAt).toLocaleString()}
                      </p>
                      <p className="text-zinc-200">{a.body}</p>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
          <p className="text-sm text-ds-text-muted">
            <Link
              href={`/admin/enterprise/proposals?leadId=${selected.id}&customer=${encodeURIComponent(selected.company || selected.name)}&email=${encodeURIComponent(selected.email)}`}
              className="text-ds-accent-lavender hover:underline"
            >
              Generate proposal for this lead →
            </Link>
          </p>
        </section>
      ) : null}
    </div>
  );
}
