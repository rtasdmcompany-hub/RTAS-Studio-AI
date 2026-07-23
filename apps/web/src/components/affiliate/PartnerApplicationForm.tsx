"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert, Button } from "@rtas/ui";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";
import { PARTNER_TYPES, type PartnerTypeId } from "@/lib/affiliate/constants";

const fieldClass =
  "mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text";

type Props = {
  defaultPartnerType?: PartnerTypeId | "";
};

export function PartnerApplicationForm({ defaultPartnerType = "" }: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [organization, setOrganization] = useState("");
  const [role, setRole] = useState("");
  const [website, setWebsite] = useState("");
  const [partnerType, setPartnerType] = useState<string>(defaultPartnerType);
  const [message, setMessage] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!acceptTerms) {
      setError("Please accept the Terms of Service and Privacy Policy.");
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/partners/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email,
          organization,
          role,
          website,
          partnerType,
          message,
          acceptTerms,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        message?: string;
      };
      if (!res.ok) {
        setError(
          data.error ||
            `Could not submit. Please try again or email ${SITE_SUPPORT_EMAIL}.`
        );
        return;
      }
      setSuccess(
        data.message ||
          `Thanks — your partnership application was received. We will reply to ${email}.`
      );
      setName("");
      setEmail("");
      setOrganization("");
      setRole("");
      setWebsite("");
      setPartnerType(defaultPartnerType);
      setMessage("");
      setAcceptTerms(false);
    } catch {
      setError(`Network error. Please email ${SITE_SUPPORT_EMAIL} directly.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="space-y-5 text-left" onSubmit={onSubmit} noValidate>
      {error ? (
        <Alert variant="error" message={error} onDismiss={() => setError(null)} />
      ) : null}
      {success ? (
        <Alert variant="success" message={success} onDismiss={() => setSuccess(null)} />
      ) : null}

      <p className="text-sm text-ds-text-muted">
        Applications are reviewed individually. We do not publish partner logos or counts until a
        signed agreement exists.
      </p>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Full name</span>
        <input
          className={fieldClass}
          value={name}
          onChange={(ev) => setName(ev.target.value)}
          required
          minLength={2}
          maxLength={120}
          autoComplete="name"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Work email</span>
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

      <label className="block text-sm">
        <span className="text-ds-text-muted">Organization</span>
        <input
          className={fieldClass}
          value={organization}
          onChange={(ev) => setOrganization(ev.target.value)}
          required
          minLength={2}
          maxLength={160}
          autoComplete="organization"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Role</span>
        <input
          className={fieldClass}
          value={role}
          onChange={(ev) => setRole(ev.target.value)}
          maxLength={120}
          autoComplete="organization-title"
          placeholder="e.g. Partnerships lead, Founder, CTO"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Website (optional)</span>
        <input
          type="url"
          className={fieldClass}
          value={website}
          onChange={(ev) => setWebsite(ev.target.value)}
          maxLength={240}
          placeholder="https://"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Partnership track</span>
        <select
          className={fieldClass}
          value={partnerType}
          onChange={(ev) => setPartnerType(ev.target.value)}
          required
          disabled={busy}
        >
          <option value="">Select track…</option>
          {PARTNER_TYPES.map((t) => (
            <option key={t.id} value={t.id}>
              {t.title}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Partnership opportunity</span>
        <textarea
          className={`${fieldClass} min-h-[120px]`}
          value={message}
          onChange={(ev) => setMessage(ev.target.value)}
          required
          minLength={20}
          maxLength={4000}
          placeholder="Describe collaboration, audience, and what success looks like…"
          disabled={busy}
        />
      </label>

      <label className="flex items-start gap-2 text-sm text-ds-text-muted">
        <input
          type="checkbox"
          className="mt-1"
          checked={acceptTerms}
          onChange={(ev) => setAcceptTerms(ev.target.checked)}
          disabled={busy}
          required
        />
        <span>
          I accept the{" "}
          <Link href="/terms" className="text-ds-accent-lavender underline-offset-2 hover:underline">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-ds-accent-lavender underline-offset-2 hover:underline">
            Privacy Policy
          </Link>
          .
        </span>
      </label>

      <div className="flex flex-wrap gap-3">
        <Button type="submit" variant="primary" disabled={busy}>
          {busy ? "Submitting…" : "Submit partnership application"}
        </Button>
        <a href={`mailto:${SITE_SUPPORT_EMAIL}`} className="rtas-btn-ghost rtas-ui-btn">
          Or email {SITE_SUPPORT_EMAIL}
        </a>
      </div>
    </form>
  );
}
