"use client";

import { useState } from "react";
import { PRODUCT_NAME } from "@rtas/shared";
import { Alert, Button, ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { SITE_SUPPORT_EMAIL, SITE_SOCIAL_LINKS } from "@/lib/site-links";
import { AnalyticsEvents, trackClientEvent } from "@/lib/analytics";

type Kind = "bug" | "feature" | "general" | "suggestion" | "other";

const DISCORD =
  SITE_SOCIAL_LINKS.find((l) => l.id === "discord")?.href ?? "https://discord.gg/rtas";

const RELATED = [
  { title: "Help Center", body: "Search categorized articles.", href: "/help" },
  { title: "Support tickets", body: "Trackable tickets with status.", href: "/tickets" },
  { title: "Troubleshooting", body: "Common Studio fixes.", href: "/help/troubleshooting" },
  { title: "Success Center", body: "Onboarding and retention hub.", href: "/success" },
] as const;

/**
 * Feedback + CSAT/NPS — persists via /api/feedback when DB is configured.
 */
export function FeedbackClient() {
  const [kind, setKind] = useState<Kind>("general");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [csat, setCsat] = useState<number | "">("");
  const [nps, setNps] = useState<number | "">("");
  const [busy, setBusy] = useState(false);
  const [sentHint, setSentHint] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSentHint(null);
    trackClientEvent(AnalyticsEvents.SUPPORT_CONTACTED, {
      channel: "feedback_api",
      kind,
    });

    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          email: email || undefined,
          message,
          csatScore: csat === "" ? undefined : csat,
          npsScore: nps === "" ? undefined : nps,
          source: "/feedback",
        }),
      });
      const data = (await res.json()) as {
        ok?: boolean;
        stored?: boolean;
        feedbackId?: string;
        emailSent?: boolean;
        error?: string;
        code?: string;
      };

      if (!res.ok) {
        // Fallback mailto if storage/email unavailable
        if (data.code === "EMAIL_NOT_CONFIGURED" || res.status === 503) {
          const subject = encodeURIComponent(
            `[${PRODUCT_NAME}] ${kind.toUpperCase()} — product feedback`
          );
          const body = encodeURIComponent(
            [
              `Type: ${kind}`,
              csat !== "" ? `CSAT: ${csat}/5` : null,
              nps !== "" ? `NPS: ${nps}/10` : null,
              email ? `Reply-to: ${email}` : "Reply-to: (not provided)",
              "",
              message.trim() || "(no message)",
              "",
              `— Sent from ${PRODUCT_NAME} /feedback`,
            ]
              .filter(Boolean)
              .join("\n")
          );
          window.location.href = `mailto:${SITE_SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
          setSentHint(
            `Could not store online (${data.error ?? "unavailable"}). Your email client should open as a fallback.`
          );
          return;
        }
        throw new Error(data.error || "Could not submit feedback.");
      }

      setSentHint(
        data.stored
          ? `Thanks — feedback saved${data.feedbackId ? ` (${data.feedbackId.slice(0, 8)}…)` : ""}${
              data.emailSent ? " and emailed to support" : ""
            }.`
          : "Thanks — feedback emailed to support."
      );
      setMessage("");
      setCsat("");
      setNps("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit feedback.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">Customer Success</p>
          <h1 className="text-zinc-100">Feedback, CSAT & NPS</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Report bugs, request features, share suggestions, and optionally rate CSAT (1–5)
            or NPS (0–10). Scores are stored only when you submit — we never invent survey
            results.
          </p>

          {sentHint ? (
            <Alert
              variant="info"
              className="mt-6"
              message={sentHint}
              onDismiss={() => setSentHint(null)}
            />
          ) : null}
          {error ? (
            <Alert
              variant="error"
              className="mt-6"
              message={error}
              onDismiss={() => setError(null)}
            />
          ) : null}

          <form className="mt-8 space-y-5 text-left" onSubmit={submit}>
            <label className="block text-sm">
              <span className="text-ds-text-muted">Type</span>
              <select
                className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                value={kind}
                onChange={(ev) => setKind(ev.target.value as Kind)}
              >
                <option value="general">General feedback</option>
                <option value="bug">Bug report</option>
                <option value="feature">Feature request</option>
                <option value="suggestion">Suggestion</option>
                <option value="other">Other</option>
              </select>
            </label>

            <label className="block text-sm">
              <span className="text-ds-text-muted">Your email (optional)</span>
              <input
                type="email"
                className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
                placeholder="you@company.com"
                autoComplete="email"
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm">
                <span className="text-ds-text-muted">CSAT (optional, 1–5)</span>
                <select
                  className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                  value={csat === "" ? "" : String(csat)}
                  onChange={(ev) =>
                    setCsat(ev.target.value === "" ? "" : Number(ev.target.value))
                  }
                >
                  <option value="">Skip</option>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-ds-text-muted">NPS (optional, 0–10)</span>
                <select
                  className="mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                  value={nps === "" ? "" : String(nps)}
                  onChange={(ev) =>
                    setNps(ev.target.value === "" ? "" : Number(ev.target.value))
                  }
                >
                  <option value="">Skip</option>
                  {Array.from({ length: 11 }, (_, i) => i).map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="block text-sm">
              <span className="text-ds-text-muted">Message</span>
              <textarea
                className="mt-1 min-h-[140px] w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text"
                value={message}
                onChange={(ev) => setMessage(ev.target.value)}
                required
                placeholder="What happened? What did you expect? Steps to reproduce help a lot."
              />
            </label>

            <div className="flex flex-wrap gap-3">
              <Button type="submit" variant="primary" disabled={busy}>
                {busy ? "Sending…" : "Submit feedback"}
              </Button>
              <ButtonLink href={`mailto:${SITE_SUPPORT_EMAIL}`} variant="ghost">
                Email {SITE_SUPPORT_EMAIL}
              </ButtonLink>
            </div>
          </form>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-labelledby="feedback-related">
          <InnerPageSection className="md:col-span-2 text-center pb-2">
            <h2 id="feedback-related" className="text-xl text-zinc-100">
              Related help
            </h2>
          </InnerPageSection>
          {RELATED.map((item) => (
            <InnerPageSection key={item.title}>
              <h3 className="text-lg text-zinc-100">{item.title}</h3>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                <ButtonLink href={item.href} variant="ghost">
                  Open →
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <a
              href={DISCORD}
              className="rtas-btn-ghost rtas-ui-btn"
              target="_blank"
              rel="noopener noreferrer"
            >
              Discord community
            </a>
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
