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
import {
  TICKET_CATEGORIES,
  TICKET_PRIORITIES,
} from "@/lib/customer-success/tickets";

type TicketListItem = {
  id: string;
  ticketNumber: string;
  category: string;
  priority: string;
  subject: string;
  status: string;
  createdAt: string;
  replyCount: number;
  attachmentCount: number;
};

const CATEGORY_LABEL: Record<string, string> = {
  account: "Account",
  billing: "Billing",
  credits: "Credits",
  video_generation: "Video Generation",
  templates: "Templates",
  ai_models: "AI Models",
  enterprise: "Enterprise",
  api: "API",
  security: "Security",
  technical: "Technical Issues",
  other: "Other",
};

export function TicketsClient() {
  const { status } = useSession();
  const [tickets, setTickets] = useState<TicketListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const [category, setCategory] = useState("technical");
  const [priority, setPriority] = useState("medium");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [attachName, setAttachName] = useState("");

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/support/tickets");
      const data = (await res.json()) as {
        ok?: boolean;
        tickets?: TicketListItem[];
        error?: string;
      };
      if (!res.ok) throw new Error(data.error || "Could not load tickets.");
      setTickets(data.tickets ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load tickets.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (status === "authenticated") void load();
  }, [status, load]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setCreatedId(null);
    try {
      const attachments = attachName.trim()
        ? [
            {
              fileName: attachName.trim(),
              contentType: "application/octet-stream",
              sizeBytes: 0,
            },
          ]
        : [];
      const res = await fetch("/api/support/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category,
          priority,
          subject,
          description,
          attachments,
        }),
      });
      const data = (await res.json()) as {
        ok?: boolean;
        ticket?: { id: string; ticketNumber: string };
        error?: string;
      };
      if (!res.ok) throw new Error(data.error || "Could not create ticket.");
      setCreatedId(data.ticket?.id ?? null);
      setSubject("");
      setDescription("");
      setAttachName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create ticket.");
    } finally {
      setBusy(false);
    }
  }

  if (status === "loading") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection>
            <p className="text-ds-text-muted">Checking session…</p>
          </InnerPageSection>
        </InnerPageContainer>
      </MarketingLayout>
    );
  }

  if (status !== "authenticated") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection className="text-center">
            <h1 className="text-zinc-100">Support tickets</h1>
            <p className="mt-3 text-ds-text-muted">
              Sign in to create and track tickets. We do not invent ticket history.
            </p>
            <div className="mt-6">
              <ButtonLink href="/auth/login?callbackUrl=/tickets" variant="lavender">
                Sign in
              </ButtonLink>
            </div>
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
            <Link href="/success" className="text-ds-accent-lavender">
              Success Center
            </Link>{" "}
            · Support
          </p>
          <h1 className="text-zinc-100">Support tickets</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Open a ticket with category, priority, subject, and description. Attachment
            fields store metadata only until a file upload pipeline is connected. Empty list
            means you have no tickets yet.
          </p>
        </InnerPageSection>

        {error ? (
          <Alert variant="error" message={error} onDismiss={() => setError(null)} />
        ) : null}
        {createdId ? (
          <Alert
            variant="success"
            message="Ticket created."
            onDismiss={() => setCreatedId(null)}
          />
        ) : null}

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">New ticket</h2>
          <form className="mt-6 space-y-4 text-left" onSubmit={submit}>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm">
                <span className="text-ds-text-muted">Category</span>
                <select
                  className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {TICKET_CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {CATEGORY_LABEL[c] ?? c}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-ds-text-muted">Priority</span>
                <select
                  className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  {TICKET_PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="block text-sm">
              <span className="text-ds-text-muted">Subject</span>
              <input
                required
                className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                maxLength={200}
              />
            </label>
            <label className="block text-sm">
              <span className="text-ds-text-muted">Description</span>
              <textarea
                required
                className="mt-1 min-h-[120px] w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={8000}
              />
            </label>
            <label className="block text-sm">
              <span className="text-ds-text-muted">
                Attachment name (metadata only — optional)
              </span>
              <input
                className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                value={attachName}
                onChange={(e) => setAttachName(e.target.value)}
                placeholder="e.g. screenshot.png"
                maxLength={200}
              />
            </label>
            <Button type="submit" variant="primary" disabled={busy}>
              {busy ? "Submitting…" : "Create ticket"}
            </Button>
          </form>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Your tickets</h2>
          {tickets.length === 0 ? (
            <p className="mt-4 text-sm text-ds-text-muted">
              No tickets yet. Create one above when you need help.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {tickets.map((t) => (
                <li key={t.id}>
                  <Link
                    href={`/tickets/${t.id}`}
                    className="inner-page-section block transition hover:border-ds-accent-lavender/40"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <span className="font-medium text-zinc-100">{t.subject}</span>
                      <span className="text-xs text-ds-text-muted">{t.ticketNumber}</span>
                    </div>
                    <p className="mt-1 text-sm text-ds-text-muted">
                      {CATEGORY_LABEL[t.category] ?? t.category} · {t.priority} · {t.status} ·{" "}
                      {t.replyCount} replies
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
