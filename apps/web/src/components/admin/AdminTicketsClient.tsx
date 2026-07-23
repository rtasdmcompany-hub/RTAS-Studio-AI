"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Alert, Button, Card } from "@rtas/ui";

const ADMIN_KEY = "rtas_admin_secret";

type AdminTicket = {
  id: string;
  ticketNumber: string;
  category: string;
  priority: string;
  subject: string;
  status: string;
  adminNotes: string;
  createdAt: string;
  user: { id: string; email: string | null; tier: string };
  replyCount: number;
};

export function AdminTicketsClient() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");
  const [tickets, setTickets] = useState<AdminTicket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<AdminTicket | null>(null);
  const [adminNotes, setAdminNotes] = useState("");
  const [status, setStatus] = useState("in_progress");
  const [replyBody, setReplyBody] = useState("");
  const [replyInternal, setReplyInternal] = useState(false);

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
  }, []);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/tickets", {
        headers: { "x-rtas-admin-secret": adminSecret },
      });
      const data = (await res.json()) as {
        ok?: boolean;
        tickets?: AdminTicket[];
        error?: string;
      };
      if (!res.ok || !data.ok) {
        throw new Error(data.error ?? "Unauthorized or unavailable.");
      }
      setTickets(data.tickets ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load tickets.");
      setTickets([]);
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

  async function saveTicket(e: React.FormEvent) {
    e.preventDefault();
    if (!selected || !stored) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/tickets", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "x-rtas-admin-secret": stored,
        },
        body: JSON.stringify({
          ticketId: selected.id,
          status,
          adminNotes,
          replyBody: replyBody || undefined,
          replyInternal,
        }),
      });
      const data = (await res.json()) as { ok?: boolean; error?: string };
      if (!res.ok || !data.ok) throw new Error(data.error ?? "Update failed.");
      setReplyBody("");
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
        <h1 className="text-xl text-zinc-100">Admin · Support tickets</h1>
        <p className="mt-2 text-sm text-ds-text-muted">
          Enter RTAS admin secret. Ticket list is empty until real customers open tickets.
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
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Support tickets</h1>
          <p className="text-sm text-ds-text-muted">
            Live tickets only — no seed data. Admin notes stay internal.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/admin" className="rtas-btn-ghost rtas-ui-btn">
            Ops dashboard
          </Link>
          <Button variant="ghost" disabled={busy} onClick={() => void load(stored)}>
            Refresh
          </Button>
        </div>
      </div>

      {error ? <Alert variant="error" message={error} /> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-4">
          <h2 className="text-lg text-zinc-100">Queue ({tickets.length})</h2>
          {tickets.length === 0 ? (
            <p className="mt-3 text-sm text-ds-text-muted">
              No tickets yet. Empty is correct until a real user creates one.
            </p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {tickets.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    className="w-full rounded-md border border-ds-border px-3 py-2 text-left hover:border-ds-accent-lavender/40"
                    onClick={() => {
                      setSelected(t);
                      setAdminNotes(t.adminNotes);
                      setStatus(t.status);
                    }}
                  >
                    <span className="font-medium text-zinc-100">{t.subject}</span>
                    <span className="mt-1 block text-xs text-ds-text-muted">
                      {t.ticketNumber} · {t.status} · {t.priority} · {t.user.email}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="p-4">
          <h2 className="text-lg text-zinc-100">Ticket detail</h2>
          {!selected ? (
            <p className="mt-3 text-sm text-ds-text-muted">Select a ticket from the queue.</p>
          ) : (
            <form className="mt-4 space-y-3" onSubmit={saveTicket}>
              <p className="text-sm text-ds-text-muted">
                {selected.ticketNumber} · {selected.category} · {selected.replyCount} replies
              </p>
              <label className="block text-sm">
                <span className="text-ds-text-muted">Status</span>
                <select
                  className="mt-1 w-full rounded-md border border-ds-border bg-ds-surface px-3 py-2"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  {[
                    "open",
                    "in_progress",
                    "waiting_on_customer",
                    "resolved",
                    "closed",
                  ].map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-ds-text-muted">Admin notes (internal)</span>
                <textarea
                  className="mt-1 min-h-[80px] w-full rounded-md border border-ds-border bg-ds-surface px-3 py-2"
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                />
              </label>
              <label className="block text-sm">
                <span className="text-ds-text-muted">Reply to customer (optional)</span>
                <textarea
                  className="mt-1 min-h-[80px] w-full rounded-md border border-ds-border bg-ds-surface px-3 py-2"
                  value={replyBody}
                  onChange={(e) => setReplyBody(e.target.value)}
                />
              </label>
              <label className="flex items-center gap-2 text-sm text-ds-text-muted">
                <input
                  type="checkbox"
                  checked={replyInternal}
                  onChange={(e) => setReplyInternal(e.target.checked)}
                />
                Internal note only (hidden from customer)
              </label>
              <Button type="submit" variant="primary" disabled={busy}>
                Save
              </Button>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
}
