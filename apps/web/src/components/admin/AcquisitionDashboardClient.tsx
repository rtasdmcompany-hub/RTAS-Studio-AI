"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card } from "@rtas/ui";
import { AdminLoadError, AdminUnlockGate } from "@/components/admin/AdminUnlockGate";
import type { AcquisitionMetrics } from "@/lib/launch/acquisition";

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

export function AcquisitionDashboardClient() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<AcquisitionMetrics | null>(null);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/acquisition", {
        headers: { "x-rtas-admin-secret": adminSecret },
      });
      const data = (await res.json()) as {
        ok?: boolean;
        error?: string;
        metrics?: AcquisitionMetrics;
      };
      if (!res.ok || !data.ok) {
        throw new Error(data.error ?? "Acquisition dashboard unauthorized.");
      }
      setMetrics(data.metrics ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load acquisition data.");
      setMetrics(null);
    } finally {
      setBusy(false);
    }
  }, []);

  return (
    <AdminUnlockGate
      title="Customer Acquisition"
      description="Enter your RTAS admin secret to view live funnel aggregates (zeros are valid)."
    >
      {(stored, clear) => (
        <AcquisitionBody
          stored={stored}
          clear={clear}
          busy={busy}
          error={error}
          metrics={metrics}
          onLoad={load}
        />
      )}
    </AdminUnlockGate>
  );
}

function AcquisitionBody({
  stored,
  clear,
  busy,
  error,
  metrics,
  onLoad,
}: {
  stored: string;
  clear: () => void;
  busy: boolean;
  error: string | null;
  metrics: AcquisitionMetrics | null;
  onLoad: (secret: string) => Promise<void>;
}) {
  useEffect(() => {
    void onLoad(stored);
  }, [stored, onLoad]);

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Customer Acquisition Dashboard</h1>
          <p className="text-sm text-ds-text-muted">
            Real registrations, verification, activation, and paid signals — never invented traffic.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" disabled={busy} onClick={() => void onLoad(stored)}>
            Refresh
          </Button>
          <Button variant="ghost" onClick={clear}>
            Lock
          </Button>
        </div>
      </div>

      <AdminLoadError message={error} />

      {metrics ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Visitors"
              value="—"
              hint={metrics.visitors.note}
            />
            <MetricCard label="Registrations" value={metrics.registrations} />
            <MetricCard label="Verified" value={metrics.verified} />
            <MetricCard label="Activated" value={metrics.activated} />
            <MetricCard label="Free" value={metrics.free} />
            <MetricCard label="Paid signals" value={metrics.paid} />
            <MetricCard label="Enterprise leads" value={metrics.enterpriseLeads} />
            <MetricCard
              label="Visitor status"
              value={metrics.visitors.status === "ready_for_integration" ? "RFI" : "Live"}
              hint="Ready for Integration until GA4/PostHog sink is live"
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Funnel</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {metrics.funnel.map((row) => (
                  <li key={row.stage} className="flex justify-between gap-2">
                    <span className="text-ds-text-muted">{row.stage}</span>
                    <span className="text-zinc-100">{row.count}</span>
                  </li>
                ))}
              </ul>
            </Card>
            <Card className="p-4">
              <h2 className="text-lg text-zinc-100">Enterprise lead sources</h2>
              {metrics.sources.length === 0 ? (
                <p className="mt-3 text-sm text-ds-text-muted">No leads yet (zero is valid).</p>
              ) : (
                <ul className="mt-3 space-y-2 text-sm">
                  {metrics.sources.map((s) => (
                    <li key={s.source} className="flex justify-between gap-2">
                      <span className="text-ds-text-muted">{s.source}</span>
                      <span className="text-zinc-100">{s.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>

          <p className="text-xs text-ds-text-muted">{metrics.integrityNote}</p>
          <p className="text-xs text-ds-text-muted">
            Generated {new Date(metrics.generatedAt).toLocaleString()} ·{" "}
            <Link href="/admin" className="underline underline-offset-2">
              Ops
            </Link>{" "}
            ·{" "}
            <Link href="/admin/launch" className="underline underline-offset-2">
              Executive
            </Link>{" "}
            ·{" "}
            <Link href="/launch" className="underline underline-offset-2">
              Launch Center
            </Link>
          </p>
        </>
      ) : null}
    </div>
  );
}
