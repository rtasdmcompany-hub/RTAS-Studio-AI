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

type Kind = "bug" | "feature" | "feedback" | "other";

const DISCORD =
  SITE_SOCIAL_LINKS.find((l) => l.id === "discord")?.href ?? "https://discord.gg/rtas";

const RELATED = [
  {
    title: "Help FAQ",
    body: "Credits, downloads, sign-in, and first-project answers.",
    href: "/help/faq",
  },
  {
    title: "Troubleshooting",
    body: "Fix common Studio and account issues without developer tools.",
    href: "/help/troubleshooting",
  },
  {
    title: "Changelog",
    body: "See what shipped recently before filing a duplicate report.",
    href: "/help/changelog",
  },
  {
    title: "Contact support",
    body: "Email, Discord community, and other support channels.",
    href: "/help/contact",
  },
] as const;

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
    window.location.href = `mailto:${SITE_SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
    setSentHint(
      `Your email client should open with a pre-filled message. If nothing opens, email ${SITE_SUPPORT_EMAIL} directly.`
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
            message. This form opens your email client with a pre-filled note so nothing is
            stored without your consent.
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
              <ButtonLink href={`mailto:${SITE_SUPPORT_EMAIL}`} variant="ghost">
                Email {SITE_SUPPORT_EMAIL}
              </ButtonLink>
            </div>
          </form>
        </InnerPageSection>

        <section
          className="grid gap-4 md:grid-cols-2"
          aria-labelledby="feedback-related"
        >
          <InnerPageSection className="md:col-span-2 text-center pb-2">
            <h2 id="feedback-related" className="text-xl text-zinc-100">
              Related help
            </h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
              Prefer self-serve when you can — or reach the team through Discord and Support
              email.
            </p>
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
          <h2 className="text-xl text-zinc-100">Other ways to reach us</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            For account-sensitive billing, use email. For product tips and community
            discussion, join Discord.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href={`mailto:${SITE_SUPPORT_EMAIL}`} variant="lavender">
              {SITE_SUPPORT_EMAIL}
            </ButtonLink>
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
