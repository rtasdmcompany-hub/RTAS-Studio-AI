"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert, Button } from "@rtas/ui";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";
import { trackClientEvent } from "@/lib/analytics";
import { AnalyticsEvents } from "@/lib/analytics/events";

export type MarketingSubscribeKind =
  | "newsletter"
  | "early_access"
  | "product_updates"
  | "ai_tips";

type Props = {
  kind?: MarketingSubscribeKind;
  title?: string;
  description?: string;
  source?: string;
  compact?: boolean;
  allowKindSelect?: boolean;
};

const KIND_OPTIONS: Array<{ value: MarketingSubscribeKind; label: string }> = [
  { value: "newsletter", label: "Newsletter" },
  { value: "product_updates", label: "Product updates" },
  { value: "ai_tips", label: "AI tips" },
  { value: "early_access", label: "Early access" },
];

const fieldClass =
  "mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text";

export function MarketingSubscribeForm({
  kind: initialKind = "newsletter",
  title = "Stay in the loop",
  description = "Product updates and practical AI video tips. No spam. Unsubscribe anytime by emailing us.",
  source = "footer",
  compact = false,
  allowKindSelect = false,
}: Props) {
  const [kind, setKind] = useState<MarketingSubscribeKind>(initialKind);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!consent) {
      setError("Please accept the Privacy Policy notice to subscribe.");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/leads/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          email,
          name: name || undefined,
          source,
          consentPrivacy: true,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        ok?: boolean;
      };
      if (!res.ok) {
        setError(
          data.error ||
            `Could not subscribe. Email ${SITE_SUPPORT_EMAIL} instead.`
        );
        return;
      }
      trackClientEvent(AnalyticsEvents.LEAD_CAPTURED, { kind, source });
      setSuccess(`You’re on the list. We’ll write to ${email} when we have updates.`);
      setEmail("");
      setName("");
      setConsent(false);
    } catch {
      setError(`Network error. Please email ${SITE_SUPPORT_EMAIL}.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      className={compact ? "rtas-subscribe rtas-subscribe--compact" : "rtas-subscribe"}
      onSubmit={onSubmit}
      noValidate
      aria-label={title}
    >
      {!compact ? (
        <div className="rtas-subscribe__head">
          <h3 className="rtas-subscribe__title">{title}</h3>
          <p className="rtas-subscribe__desc">{description}</p>
        </div>
      ) : (
        <p className="rtas-subscribe__title">{title}</p>
      )}

      {error ? (
        <Alert variant="error" message={error} onDismiss={() => setError(null)} />
      ) : null}
      {success ? (
        <Alert
          variant="success"
          message={success}
          onDismiss={() => setSuccess(null)}
        />
      ) : null}

      {allowKindSelect ? (
        <label className="block text-sm">
          <span className="text-ds-text-muted">List</span>
          <select
            className={fieldClass}
            value={kind}
            onChange={(ev) => setKind(ev.target.value as MarketingSubscribeKind)}
            disabled={busy}
          >
            {KIND_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {!compact ? (
        <label className="block text-sm">
          <span className="text-ds-text-muted">Name (optional)</span>
          <input
            className={fieldClass}
            value={name}
            onChange={(ev) => setName(ev.target.value)}
            maxLength={120}
            autoComplete="name"
            disabled={busy}
          />
        </label>
      ) : null}

      <label className="block text-sm">
        <span className="text-ds-text-muted">Email</span>
        <input
          type="email"
          className={fieldClass}
          value={email}
          onChange={(ev) => setEmail(ev.target.value)}
          required
          maxLength={254}
          autoComplete="email"
          disabled={busy}
        />
      </label>

      <label className="mt-2 flex items-start gap-2 text-xs text-ds-text-muted">
        <input
          type="checkbox"
          className="mt-0.5"
          checked={consent}
          onChange={(ev) => setConsent(ev.target.checked)}
          disabled={busy}
          required
        />
        <span>
          I agree to receive {KIND_OPTIONS.find((o) => o.value === kind)?.label.toLowerCase()}{" "}
          emails and accept the{" "}
          <Link href="/privacy" className="text-ds-accent-lavender underline-offset-2 hover:underline">
            Privacy Policy
          </Link>
          . This is not a free credit plan — generation requires paid Tester or a subscription.
        </span>
      </label>

      <div className="mt-3">
        <Button type="submit" variant="primary" disabled={busy}>
          {busy ? "Subscribing…" : "Subscribe"}
        </Button>
      </div>
    </form>
  );
}
