"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Alert, Button } from "@rtas/ui";
import { buildProposalMarkdown, nextProposalNumber } from "@/lib/enterprise/proposal";

const ADMIN_KEY = "rtas_admin_secret";

const fieldClass =
  "mt-1 w-full rounded-md border border-ds-border-subtle bg-ds-surface-glass px-3 py-2 text-sm text-zinc-100";

export function ProposalGeneratorClient() {
  const search = useSearchParams();
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState("");
  const [customerContact, setCustomerContact] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [leadId, setLeadId] = useState("");
  const [requirements, setRequirements] = useState("");
  const [solution, setSolution] = useState("");
  const [timeline, setTimeline] = useState("");
  const [pricingNotes, setPricingNotes] = useState("");
  const [supportNotes, setSupportNotes] = useState("");
  const [acceptanceNotes, setAcceptanceNotes] = useState("");
  const [markdown, setMarkdown] = useState("");
  const [proposalNumber, setProposalNumber] = useState(nextProposalNumber(0));

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
    const c = search.get("customer");
    const e = search.get("email");
    const l = search.get("leadId");
    if (c) setCustomerName(c);
    if (e) setCustomerEmail(e);
    if (l) setLeadId(l);
  }, [search]);

  const preview = useMemo(() => {
    if (!customerName.trim()) return "";
    return buildProposalMarkdown({
      proposalNumber,
      customerName: customerName.trim(),
      customerContact: customerContact.trim() || undefined,
      customerEmail: customerEmail.trim() || undefined,
      requirements: requirements.trim() || undefined,
      solution: solution.trim() || undefined,
      timeline: timeline.trim() || undefined,
      pricingNotes: pricingNotes.trim() || undefined,
      supportNotes: supportNotes.trim() || undefined,
      acceptanceNotes: acceptanceNotes.trim() || undefined,
    });
  }, [
    proposalNumber,
    customerName,
    customerContact,
    customerEmail,
    requirements,
    solution,
    timeline,
    pricingNotes,
    supportNotes,
    acceptanceNotes,
  ]);

  function unlock(e: React.FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;
    sessionStorage.setItem(ADMIN_KEY, secret.trim());
    setStored(secret.trim());
  }

  function downloadMarkdown(content: string, filename: string) {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function generate(persist: boolean) {
    if (!stored) return;
    if (!customerName.trim()) {
      setError("Customer name is required.");
      return;
    }
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/admin/enterprise/proposals", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-rtas-admin-secret": stored,
        },
        body: JSON.stringify({
          persist,
          leadId: leadId || undefined,
          proposalNumber,
          customerName: customerName.trim(),
          customerContact: customerContact.trim() || undefined,
          customerEmail: customerEmail.trim() || undefined,
          requirements: requirements.trim() || undefined,
          solution: solution.trim() || undefined,
          timeline: timeline.trim() || undefined,
          pricingNotes: pricingNotes.trim() || undefined,
          supportNotes: supportNotes.trim() || undefined,
          acceptanceNotes: acceptanceNotes.trim() || undefined,
        }),
      });
      const data = (await res.json()) as {
        ok?: boolean;
        error?: string;
        proposal?: { markdownBody: string; proposalNumber: string; id?: string };
      };
      if (!res.ok || !data.ok || !data.proposal) {
        throw new Error(data.error || "Could not generate proposal.");
      }
      setMarkdown(data.proposal.markdownBody);
      setProposalNumber(data.proposal.proposalNumber);
      setSuccess(
        persist
          ? `Proposal ${data.proposal.proposalNumber} saved.`
          : `Proposal ${data.proposal.proposalNumber} generated (not persisted).`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!stored) {
    return (
      <div className="mx-auto max-w-md p-6">
        <h1 className="text-xl text-zinc-100">Proposal generator</h1>
        <p className="mt-2 text-sm text-ds-text-muted">
          Admin secret required. Output is markdown / PDF-friendly — no invented metrics.
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
            Unlock
          </Button>
        </form>
      </div>
    );
  }

  const body = markdown || preview;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">Enterprise proposal generator</h1>
          <p className="text-sm text-ds-text-muted">
            Template: customer, requirements, solution, timeline, pricing, support, acceptance.
          </p>
        </div>
        <Link href="/admin/enterprise" className="rtas-btn-ghost rtas-ui-btn">
          ← CRM
        </Link>
      </div>

      {error ? <Alert variant="error" message={error} /> : null}
      {success ? <Alert variant="success" message={success} /> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            void generate(true);
          }}
        >
          <label className="block text-sm text-ds-text-muted">
            Proposal number
            <input
              className={fieldClass}
              value={proposalNumber}
              onChange={(e) => setProposalNumber(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Customer / company
            <input
              className={fieldClass}
              required
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Attention / contact
            <input
              className={fieldClass}
              value={customerContact}
              onChange={(e) => setCustomerContact(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Customer email
            <input
              type="email"
              className={fieldClass}
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            CRM lead id (optional)
            <input
              className={fieldClass}
              value={leadId}
              onChange={(e) => setLeadId(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Requirements
            <textarea
              className={`${fieldClass} min-h-[90px]`}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Solution
            <textarea
              className={`${fieldClass} min-h-[90px]`}
              value={solution}
              onChange={(e) => setSolution(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Timeline
            <textarea
              className={`${fieldClass} min-h-[70px]`}
              value={timeline}
              onChange={(e) => setTimeline(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Pricing notes
            <textarea
              className={`${fieldClass} min-h-[70px]`}
              value={pricingNotes}
              onChange={(e) => setPricingNotes(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Support notes
            <textarea
              className={`${fieldClass} min-h-[70px]`}
              value={supportNotes}
              onChange={(e) => setSupportNotes(e.target.value)}
            />
          </label>
          <label className="block text-sm text-ds-text-muted">
            Acceptance notes
            <textarea
              className={`${fieldClass} min-h-[70px]`}
              value={acceptanceNotes}
              onChange={(e) => setAcceptanceNotes(e.target.value)}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" variant="primary" disabled={busy}>
              {busy ? "Saving…" : "Save proposal"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={busy}
              onClick={() => void generate(false)}
            >
              Preview only
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={!body}
              onClick={() =>
                downloadMarkdown(body, `${proposalNumber || "proposal"}.md`)
              }
            >
              Download .md
            </Button>
          </div>
        </form>

        <div>
          <h2 className="text-lg text-zinc-100">Markdown preview (PDF-friendly)</h2>
          <pre className="mt-3 max-h-[70vh] overflow-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-black/30 p-4 text-xs text-zinc-200">
            {body || "Enter a customer name to preview the template…"}
          </pre>
        </div>
      </div>
    </div>
  );
}
