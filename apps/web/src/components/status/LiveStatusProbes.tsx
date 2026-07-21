"use client";

import { useEffect, useState } from "react";
import { ButtonLink } from "@rtas/ui";

type Probe = {
  name: string;
  url: string;
  status?: number;
  ok?: boolean;
  snippet?: string;
  error?: string;
};

export function LiveStatusProbes() {
  const [probes, setProbes] = useState<Probe[]>([]);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    const targets: Probe[] = [
      { name: "Web health", url: "/api/health" },
      { name: "Readiness", url: "/api/ready" },
      { name: "Auth config", url: "/api/auth/config" },
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
            snippet: text.slice(0, 120),
          });
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
    <section className="space-y-3" aria-label="Live probes">
      <h2 className="text-lg text-zinc-100">Live probes</h2>
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
                <span className="font-medium text-zinc-100">{p.name}</span>
                <span
                  className={
                    p.ok
                      ? "text-emerald-400"
                      : "text-amber-400"
                  }
                >
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
