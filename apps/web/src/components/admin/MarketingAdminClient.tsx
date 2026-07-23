"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Alert, Button, Card } from "@rtas/ui";
import type { EmailTemplateMeta } from "@/lib/marketing/email-templates";
import type { SegmentCount } from "@/lib/marketing/segmentation";
import type { CampaignRow } from "@/lib/marketing/campaigns";

const ADMIN_KEY = "rtas_admin_secret";

type MarketingPayload = {
  ok?: boolean;
  error?: string;
  integrity?: {
    note: string;
    espMetrics: string;
    emailDeliveryConfigured: boolean;
    emailDeliveryMode: string;
  };
  templates?: EmailTemplateMeta[];
  segments?: SegmentCount[];
  campaigns?: CampaignRow[];
  queue?: { queued: number; scheduled: number; sending: number };
  newsletterSubscribers?: number;
  recentSends?: Array<{
    id: string;
    templateId: string;
    toEmail: string;
    subject: string;
    status: string;
    provider: string | null;
    createdAt: string;
  }>;
};

function Metric({
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

export function MarketingAdminClient() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<MarketingPayload | null>(null);

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
  }, []);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/marketing", {
        headers: { "x-rtas-admin-secret": adminSecret },
      });
      const json = (await res.json()) as MarketingPayload;
      if (!res.ok || !json.ok) {
        throw new Error(json.error ?? "Unauthorized or unavailable.");
      }
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed.");
      setData(null);
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
        <h1 className="text-xl text-zinc-100">Marketing Admin</h1>
        <p className="mt-2 text-sm text-ds-text-muted">
          Enter RTAS admin secret to open the Email Marketing Center.
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
            Unlock
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Email Marketing Center</h1>
          <p className="text-sm text-ds-text-muted">
            Templates, segments, campaigns — live counts only. ESP open/click = Not connected.
          </p>
        </div>
        <div className="flex gap-2">
          <ButtonLinkLike href="/admin" />
          <Button variant="ghost" disabled={busy} onClick={() => void load(stored)}>
            Refresh
          </Button>
        </div>
      </div>

      {error && <Alert variant="error" message={error} />}

      {data?.integrity && (
        <Alert
          variant="info"
          message={`${data.integrity.note} Delivery: ${data.integrity.emailDeliveryMode} (${data.integrity.emailDeliveryConfigured ? "configured" : "not configured"}). ESP metrics: ${data.integrity.espMetrics}.`}
        />
      )}

      {data && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric
              label="Newsletter subscribers"
              value={data.newsletterSubscribers ?? 0}
            />
            <Metric label="Queue" value={data.queue?.queued ?? 0} />
            <Metric label="Scheduled" value={data.queue?.scheduled ?? 0} />
            <Metric label="Sending" value={data.queue?.sending ?? 0} />
          </section>

          <section>
            <h2 className="mb-3 text-lg text-zinc-100">Customer segments</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {(data.segments ?? []).map((s) => (
                <Card key={s.id} className="p-4">
                  <p className="text-xs uppercase text-ds-text-muted">{s.name}</p>
                  <p className="mt-1 text-xl font-semibold text-zinc-100">
                    {s.count === null ? "N/A" : s.count}
                  </p>
                  {s.note ? (
                    <p className="mt-1 text-xs text-ds-text-muted">{s.note}</p>
                  ) : null}
                </Card>
              ))}
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-lg text-zinc-100">Campaigns</h2>
            <div className="overflow-x-auto rounded-xl border border-white/10">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-white/5 text-ds-text-muted">
                  <tr>
                    <th className="px-3 py-2 font-medium">Campaign</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                    <th className="px-3 py-2 font-medium">Subscribers</th>
                    <th className="px-3 py-2 font-medium">Sent</th>
                    <th className="px-3 py-2 font-medium">Open</th>
                    <th className="px-3 py-2 font-medium">Click</th>
                    <th className="px-3 py-2 font-medium">Bounce</th>
                    <th className="px-3 py-2 font-medium">Unsub</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.campaigns ?? []).map((c) => (
                    <tr key={c.id} className="border-t border-white/5 text-zinc-200">
                      <td className="px-3 py-2">
                        <div>{c.name}</div>
                        {c.note ? (
                          <div className="text-xs text-ds-text-muted">{c.note}</div>
                        ) : null}
                      </td>
                      <td className="px-3 py-2">{c.status}</td>
                      <td className="px-3 py-2">{c.metrics.subscribers}</td>
                      <td className="px-3 py-2">{c.metrics.sent}</td>
                      <td className="px-3 py-2">
                        {c.metrics.opens === null
                          ? "Not connected"
                          : c.metrics.opens}
                      </td>
                      <td className="px-3 py-2">
                        {c.metrics.clicks === null
                          ? "Not connected"
                          : c.metrics.clicks}
                      </td>
                      <td className="px-3 py-2">
                        {c.metrics.bounces === null
                          ? "Not connected"
                          : c.metrics.bounces}
                      </td>
                      <td className="px-3 py-2">{c.metrics.unsubscribes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-lg text-zinc-100">Template registry</h2>
            <div className="grid gap-3 md:grid-cols-2">
              {(data.templates ?? []).map((t) => (
                <Card key={t.id} className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-zinc-100">{t.name}</p>
                    <span
                      className={`shrink-0 rounded px-2 py-0.5 text-xs ${
                        t.hookStatus === "live"
                          ? "bg-emerald-500/15 text-emerald-300"
                          : "bg-amber-500/15 text-amber-200"
                      }`}
                    >
                      {t.hookStatus === "live" ? "Live hook" : "Planned"}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-ds-text-muted">{t.description}</p>
                  <p className="mt-2 text-xs text-ds-text-muted">Trigger: {t.trigger}</p>
                </Card>
              ))}
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-lg text-zinc-100">Recent sends</h2>
            <Card className="p-4">
              {(data.recentSends ?? []).length === 0 ? (
                <p className="text-sm text-ds-text-muted">
                  No send logs yet (0). Logs appear after migration + real sends.
                </p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {data.recentSends!.map((s) => (
                    <li key={s.id} className="flex flex-wrap justify-between gap-2">
                      <span className="text-ds-text-muted">
                        {s.templateId} → {s.toEmail}
                      </span>
                      <span className="text-zinc-300">
                        {s.status}
                        {s.provider ? ` · ${s.provider}` : ""} ·{" "}
                        {new Date(s.createdAt).toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>
        </>
      )}
    </div>
  );
}

function ButtonLinkLike({ href }: { href: string }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center rounded-md border border-white/10 px-3 py-2 text-sm text-zinc-200 hover:bg-white/5"
    >
      Ops dashboard
    </Link>
  );
}
