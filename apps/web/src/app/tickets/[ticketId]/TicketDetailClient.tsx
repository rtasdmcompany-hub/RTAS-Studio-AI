"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { Alert, Button, ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

type Ticket = {
  id: string;
  ticketNumber: string;
  category: string;
  priority: string;
  subject: string;
  description: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  attachments: Array<{ id: string; fileName: string; sizeBytes: number }>;
  replies: Array<{
    id: string;
    authorRole: string;
    body: string;
    createdAt: string;
  }>;
};

export function TicketDetailClient({ ticketId }: { ticketId: string }) {
  const { status } = useSession();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/support/tickets/${ticketId}`);
      const data = (await res.json()) as {
        ok?: boolean;
        ticket?: Ticket;
        error?: string;
      };
      if (!res.ok) throw new Error(data.error || "Ticket not found.");
      setTicket(data.ticket ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load ticket.");
    } finally {
      setBusy(false);
    }
  }, [ticketId]);

  useEffect(() => {
    if (status === "authenticated") void load();
  }, [status, load]);

  async function sendReply(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/support/tickets/${ticketId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: reply }),
      });
      const data = (await res.json()) as {
        ok?: boolean;
        ticket?: Ticket;
        error?: string;
      };
      if (!res.ok) throw new Error(data.error || "Could not send reply.");
      setTicket(data.ticket ?? null);
      setReply("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send reply.");
    } finally {
      setBusy(false);
    }
  }

  if (status !== "authenticated") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection className="text-center">
            <ButtonLink href={`/auth/login?callbackUrl=/tickets/${ticketId}`} variant="lavender">
              Sign in to view ticket
            </ButtonLink>
          </InnerPageSection>
        </InnerPageContainer>
      </MarketingLayout>
    );
  }

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">
            <Link href="/tickets" className="text-ds-accent-lavender">
              Tickets
            </Link>
          </p>
          {error ? (
            <Alert variant="error" className="mt-4" message={error} onDismiss={() => setError(null)} />
          ) : null}
          {!ticket && !error ? (
            <p className="mt-4 text-ds-text-muted">{busy ? "Loading…" : "Ticket not found."}</p>
          ) : null}
          {ticket ? (
            <>
              <h1 className="mt-2 text-zinc-100">{ticket.subject}</h1>
              <p className="mt-2 text-sm text-ds-text-muted">
                {ticket.ticketNumber} · {ticket.category} · {ticket.priority} · {ticket.status}
              </p>
              <p className="mt-2 text-xs text-ds-text-muted">
                Created {new Date(ticket.createdAt).toLocaleString()} · Updated{" "}
                {new Date(ticket.updatedAt).toLocaleString()}
              </p>
              <div className="mt-6 whitespace-pre-wrap text-sm text-ds-text-muted">
                {ticket.description}
              </div>
              {ticket.attachments.length > 0 ? (
                <ul className="mt-4 text-sm text-ds-text-muted">
                  {ticket.attachments.map((a) => (
                    <li key={a.id}>
                      Attachment: {a.fileName}
                      {a.sizeBytes ? ` (${a.sizeBytes} bytes metadata)` : ""}
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : null}
        </InnerPageSection>

        {ticket ? (
          <>
            <InnerPageSection>
              <h2 className="text-xl text-zinc-100">Conversation</h2>
              {ticket.replies.length === 0 ? (
                <p className="mt-4 text-sm text-ds-text-muted">No replies yet.</p>
              ) : (
                <ul className="mt-4 space-y-4">
                  {ticket.replies.map((r) => (
                    <li key={r.id} className="border-l border-ds-border pl-4">
                      <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                        {r.authorRole} · {new Date(r.createdAt).toLocaleString()}
                      </p>
                      <p className="mt-1 whitespace-pre-wrap text-sm text-zinc-100">{r.body}</p>
                    </li>
                  ))}
                </ul>
              )}
            </InnerPageSection>
            {ticket.status !== "closed" ? (
              <InnerPageSection>
                <h2 className="text-xl text-zinc-100">Add reply</h2>
                <form className="mt-4 space-y-3" onSubmit={sendReply}>
                  <textarea
                    required
                    className="min-h-[100px] w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                    value={reply}
                    onChange={(e) => setReply(e.target.value)}
                  />
                  <Button type="submit" variant="primary" disabled={busy}>
                    Send reply
                  </Button>
                </form>
              </InnerPageSection>
            ) : null}
          </>
        ) : null}
      </InnerPageContainer>
    </MarketingLayout>
  );
}
