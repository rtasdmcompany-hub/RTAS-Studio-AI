"use client";

import { useEffect, useState } from "react";
import { ButtonLink } from "@rtas/ui";

type Probe = {
  name: string;
  url: string;
  group: string;
  status?: number;
  ok?: boolean;
  snippet?: string;
  error?: string;
  placeholder?: boolean;
};

type PublicStatus = {
  web: string;
  api: string;
  database: string;
  storage: string;
  email: string;
  auth: string;
  billing: string;
  gpu: string;
  timestamp?: string;
};

export function LiveStatusProbes() {
  const [probes, setProbes] = useState<Probe[]>([]);
  const [summary, setSummary] = useState<PublicStatus | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    const targets: Probe[] = [
      { name: "Web health", url: "/api/health", group: "Web / API" },
      { name: "Readiness", url: "/api/ready", group: "Deps / GPU / DB / Email" },
      { name: "Auth config", url: "/api/auth/config", group: "Auth" },
      { name: "Public status summary", url: "/api/status/summary", group: "Summary" },
    ];

    void (async () => {
      const results: Probe[] = [];
      for (const t of targets) {
        try {
          const res = await fetch(t.url, { cache: "no-store" });
          const text = await res.text();
          results.push({
            ...t,
            status: res.status,
            ok: res.ok,
            snippet: text.slice(0, 160),
          });
          if (t.url === "/api/status/summary" && res.ok) {
            try {
              setSummary(JSON.parse(text) as PublicStatus);
            } catch {
              /* ignore */
            }
          }
        } catch (err) {
          results.push({
            ...t,
            ok: false,
            error: err instanceof Error ? err.message : "Probe failed",
          });
        }
      }
      setProbes(results);
      setBusy(false);
    })();
  }, []);

  return (
    <section className="space-y-4" aria-label="Live probes">
      <h2 className="text-lg text-zinc-100">Live probes</h2>
      {summary ? (
        <ul className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 text-sm">
          {(
            [
              ["Web", summary.web],
              ["API / GPU", summary.gpu],
              ["Database", summary.database],
              ["Storage", summary.storage],
              ["Email", summary.email],
              ["Auth", summary.auth],
              ["Billing", summary.billing],
            ] as const
          ).map(([label, value]) => (
            <li
              key={label}
              className="rounded-lg border border-ds-border-subtle bg-ds-surface-glass px-3 py-2"
            >
              <span className="text-zinc-100">{label}</span>
              <span className="mt-1 block text-xs text-ds-text-muted">{value}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {busy ? (
        <p className="text-sm text-ds-text-muted">Checking production endpoints…</p>
      ) : (
        <ul className="space-y-3">
          {probes.map((p) => (
            <li
              key={p.name}
              className="rounded-lg border border-ds-border-subtle bg-ds-surface-glass p-4 text-sm"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-zinc-100">
                  {p.name}
                  <span className="ml-2 text-xs font-normal text-ds-text-muted">
                    {p.group}
                  </span>
                </span>
                <span className={p.ok ? "text-emerald-400" : "text-amber-400"}>
                  {p.ok ? "OK" : "Issue"} {p.status ? `· HTTP ${p.status}` : ""}
                </span>
              </div>
              {p.error ? (
                <p className="mt-2 text-ds-text-muted">{p.error}</p>
              ) : (
                <pre className="mt-2 overflow-x-auto text-xs text-ds-text-muted">
                  {p.snippet}
                </pre>
              )}
            </li>
          ))}
        </ul>
      )}
      <ButtonLink href="/api/health" variant="ghost">
        Open raw health JSON
      </ButtonLink>
    </section>
  );
}
