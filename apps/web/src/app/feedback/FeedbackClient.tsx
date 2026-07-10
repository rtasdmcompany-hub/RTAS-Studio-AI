"use client";

import { useState } from "react";
import { PRODUCT_NAME } from "@rtas/shared";
import { Alert, Button, ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

type Kind = "bug" | "feature" | "feedback" | "other";

/**
 * Customer Success capture — mailto handoff until a ticketing backend is connected.
 * No secrets; no fake integrations.
 */
export function FeedbackClient() {
  const [kind, setKind] = useState<Kind>("feedback");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [sentHint, setSentHint] = useState<string | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const subject = encodeURIComponent(
      `[${PRODUCT_NAME}] ${kind.toUpperCase()} — product feedback`
    );
    const body = encodeURIComponent(
      [
        `Type: ${kind}`,
        email ? `Reply-to: ${email}` : "Reply-to: (not provided)",
        "",
        message.trim() || "(no message)",
        "",
        `— Sent from ${PRODUCT_NAME} /feedback`,
      ].join("\n")
    );
    window.location.href = `mailto:support@rtasdigital.com?subject=${subject}&body=${body}`;
    setSentHint(
      "Your email client should open with a pre-filled message. If nothing opens, email support@rtasdigital.com directly."
    );
  }

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection>
          <p className="rtas-eyebrow">Customer Success</p>
          <h1 className="text-zinc-100">Feedback & requests</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Tell us what broke, what delighted you, or what you need next. We read every
            message — this form opens your email client so nothing is stored without your
            consent.
          </p>

          {sentHint ? (
            <Alert
              variant="info"
              className="mt-6"
              message={sentHint}
              onDismiss={() => setSentHint(null)}
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
                <option value="feedback">General feedback</option>
                <option value="bug">Bug report</option>
                <option value="feature">Feature request</option>
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
              <Button type="submit" variant="primary">
                Open email to support
              </Button>
              <ButtonLink href="/help" variant="ghost">
                Back to Help Center
              </ButtonLink>
            </div>
          </form>
        </InnerPageSection>

        <InnerPageSection aria-labelledby="cs-placeholders">
          <h2 id="cs-placeholders" className="text-xl text-zinc-100">
            Coming soon
          </h2>
          <ul className="mt-4 grid gap-3 text-sm text-ds-text-muted md:grid-cols-2">
            <li>Knowledge Base articles</li>
            <li>Video tutorials</li>
            <li>Community forum</li>
            <li>In-app ticket status</li>
          </ul>
          <p className="mt-4 text-sm text-ds-text-muted">
            Placeholders only — no fake backends. These channels activate when Customer
            Success tooling is connected.
          </p>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
