"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card } from "@rtas/ui";
import { AdminLoadError, AdminUnlockGate } from "@/components/admin/AdminUnlockGate";
import type { LaunchChecklistItem, LaunchMilestone, ReadinessScore } from "@/lib/launch/types";

type Payload = {
  readiness: {
    dimensions: ReadinessScore[];
    overall: { score: number; label: string };
    integrityNote: string;
    generatedAt: string;
  };
  progress: {
    total: number;
    done: number;
    inProgress: number;
    blocked: number;
    pct: number;
  };
  milestones: LaunchMilestone[];
  checklist: LaunchChecklistItem[];
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

export function ExecutiveLaunchDashboardClient() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Payload | null>(null);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/launch-readiness", {
        headers: { "x-rtas-admin-secret": adminSecret },
      });
      const json = (await res.json()) as Payload & { ok?: boolean; error?: string };
      if (!res.ok || !json.ok) {
        throw new Error(json.error ?? "Executive dashboard unauthorized.");
      }
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load readiness.");
      setData(null);
    } finally {
      setBusy(false);
    }
  }, []);

  return (
    <AdminUnlockGate
      title="Executive Launch Dashboard"
      description="Admin secret required. Scores are computed from real checklist status — not invented 100%s."
    >
      {(stored, clear) => (
        <ExecutiveBody
          stored={stored}
          clear={clear}
          busy={busy}
          error={error}
          data={data}
          onLoad={load}
        />
      )}
    </AdminUnlockGate>
  );
}

function ExecutiveBody({
  stored,
  clear,
  busy,
  error,
  data,
  onLoad,
}: {
  stored: string;
  clear: () => void;
  busy: boolean;
  error: string | null;
  data: Payload | null;
  onLoad: (secret: string) => Promise<void>;
}) {
  useEffect(() => {
    void onLoad(stored);
  }, [stored, onLoad]);

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Executive Launch Dashboard</h1>
          <p className="text-sm text-ds-text-muted">
            Infra · Security · Marketing · Sales · Support · Business readiness
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

      {data ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Overall readiness"
              value={data.readiness.overall.score}
              hint={data.readiness.overall.label}
            />
            <MetricCard
              label="Checklist complete"
              value={`${data.progress.pct}%`}
              hint={`${data.progress.done}/${data.progress.total} done`}
            />
            <MetricCard label="In progress" value={data.progress.inProgress} />
            <MetricCard label="Blocked" value={data.progress.blocked} />
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.readiness.dimensions.map((d) => (
              <MetricCard
                key={d.dimension}
                label={d.label}
                value={`${d.score}/${d.max}`}
                hint={d.notes}
              />
            ))}
          </section>

          <Card className="p-4">
            <h2 className="text-lg text-zinc-100">Milestones</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {data.milestones.map((m) => (
                <li key={m.id} className="flex justify-between gap-2">
                  <span className="text-ds-text-muted">{m.title}</span>
                  <span className="shrink-0 text-zinc-300">{m.status}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card className="p-4">
            <h2 className="text-lg text-zinc-100">Full checklist (incl. internal)</h2>
            <ul className="mt-3 max-h-96 space-y-2 overflow-y-auto text-sm">
              {data.checklist.map((c) => (
                <li key={c.id} className="flex justify-between gap-2 border-b border-white/5 pb-2">
                  <span className="text-ds-text-muted">
                    {c.title}
                    {c.internal ? " (internal)" : ""}
                  </span>
                  <span className="shrink-0 text-zinc-300">
                    {c.status} · {c.owner}
                  </span>
                </li>
              ))}
            </ul>
          </Card>

          <p className="text-xs text-ds-text-muted">{data.readiness.integrityNote}</p>
          <p className="text-xs text-ds-text-muted">
            <Link href="/admin/acquisition" className="underline underline-offset-2">
              Acquisition
            </Link>{" "}
            ·{" "}
            <Link href="/admin/revenue" className="underline underline-offset-2">
              RevOps
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
