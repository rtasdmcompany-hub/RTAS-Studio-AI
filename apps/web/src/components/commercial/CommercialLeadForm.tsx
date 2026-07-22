"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert, Button } from "@rtas/ui";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";

export type CommercialLeadKind = "beta" | "enterprise" | "partners";

type Props = {
  kind: CommercialLeadKind;
  submitLabel: string;
  /** Extra fields rendered before the message / acceptance block */
  showCompany?: boolean;
  showRole?: boolean;
  showWebsite?: boolean;
  showUseCase?: boolean;
  showPartnerType?: boolean;
  showRequestType?: boolean;
  /** Prefill enterprise request type: demo | proposal | meeting | quote */
  defaultRequestType?: "demo" | "proposal" | "meeting" | "quote";
  requireTerms?: boolean;
  messageLabel?: string;
  messagePlaceholder?: string;
  messageRequired?: boolean;
  messageMinLength?: number;
  /** Label for the email field (enterprise prefers business email). */
  emailLabel?: string;
};

const PARTNER_TYPES = [
  { value: "technology", label: "Technology" },
  { value: "creative_agencies", label: "Creative Agencies" },
  { value: "enterprise", label: "Enterprise" },
  { value: "affiliate", label: "Affiliate" },
  { value: "education", label: "Education" },
] as const;

const REQUEST_TYPES = [
  { value: "demo", label: "Schedule a demo" },
  { value: "proposal", label: "Enterprise inquiry / proposal" },
  { value: "meeting", label: "Sales meeting" },
  { value: "quote", label: "Request a quote" },
] as const;

const fieldClass =
  "mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text";

export function CommercialLeadForm({
  kind,
  submitLabel,
  showCompany = false,
  showRole = false,
  showWebsite = false,
  showUseCase = false,
  showPartnerType = false,
  showRequestType = false,
  defaultRequestType = "demo",
  requireTerms = false,
  messageLabel = "Message",
  messagePlaceholder = "Tell us what you need…",
  messageRequired = false,
  messageMinLength = 0,
  emailLabel = "Work email",
}: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [website, setWebsite] = useState("");
  const [useCase, setUseCase] = useState("");
  const [partnerType, setPartnerType] = useState("");
  const [requestType, setRequestType] = useState(defaultRequestType);
  const [message, setMessage] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (messageRequired && message.trim().length < Math.max(1, messageMinLength)) {
      setError(
        `Please include a message of at least ${Math.max(1, messageMinLength)} characters.`
      );
      return;
    }
    if (requireTerms && (!acceptTerms || !acceptPrivacy)) {
      setError("Please accept the Terms of Service and Privacy Policy to continue.");
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/commercial/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          name,
          email,
          company: showCompany ? company : undefined,
          role: showRole ? role : undefined,
          website: showWebsite ? website : undefined,
          useCase: showUseCase ? useCase : undefined,
          partnerType: showPartnerType ? partnerType : undefined,
          requestType: showRequestType ? requestType : undefined,
          message: message || undefined,
          acceptTerms: requireTerms ? acceptTerms : undefined,
          acceptPrivacy: requireTerms ? acceptPrivacy : undefined,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        code?: string;
        ok?: boolean;
      };
      if (!res.ok) {
        const fallback =
          res.status === 503
            ? `Email delivery is not configured. Please write to ${SITE_SUPPORT_EMAIL} directly.`
            : "Could not submit. Please try again or email us directly.";
        setError(data.error || fallback);
        return;
      }
      setSuccess(
        `Thanks — your request was sent. We will reply to ${email}. If you need anything sooner, email ${SITE_SUPPORT_EMAIL}.`
      );
      setName("");
      setEmail("");
      setCompany("");
      setRole("");
      setWebsite("");
      setUseCase("");
      setPartnerType("");
      setRequestType(defaultRequestType);
      setMessage("");
      setAcceptTerms(false);
      setAcceptPrivacy(false);
    } catch {
      setError(
        `Network error. Please try again or email ${SITE_SUPPORT_EMAIL} directly.`
      );
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
        <span className="text-ds-text-muted">{emailLabel}</span>
        <input
          type="email"
          className={fieldClass}
          value={email}
          onChange={(ev) => setEmail(ev.target.value)}
          required
          maxLength={254}
          autoComplete="email"
          placeholder={kind === "enterprise" ? "you@company.com" : undefined}
          disabled={busy}
        />
      </label>

      {showCompany ? (
        <label className="block text-sm">
          <span className="text-ds-text-muted">
            {kind === "partners" ? "Organization" : "Company"}
          </span>
          <input
            className={fieldClass}
            value={company}
            onChange={(ev) => setCompany(ev.target.value)}
            required
            maxLength={160}
            autoComplete="organization"
            disabled={busy}
          />
        </label>
      ) : null}

      {showRole ? (
        <label className="block text-sm">
          <span className="text-ds-text-muted">Role</span>
          <input
            className={fieldClass}
            value={role}
            onChange={(ev) => setRole(ev.target.value)}
            maxLength={120}
            autoComplete="organization-title"
            placeholder="e.g. Producer, Creative Director, CTO"
            disabled={busy}
          />
        </label>
      ) : null}

      {showWebsite ? (
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
      ) : null}

      {showPartnerType ? (
        <label className="block text-sm">
          <span className="text-ds-text-muted">Partnership type</span>
          <select
            className={fieldClass}
            value={partnerType}
            onChange={(ev) => setPartnerType(ev.target.value)}
            required
            disabled={busy}
          >
            <option value="">Select type…</option>
            {PARTNER_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {showRequestType ? (
        <fieldset className="text-sm">
          <legend className="text-ds-text-muted">What do you need?</legend>
          <div className="mt-2 flex flex-col gap-2">
            {REQUEST_TYPES.map((t) => (
              <label key={t.value} className="flex items-center gap-2 text-ds-text">
                <input
                  type="radio"
                  name="requestType"
                  value={t.value}
                  checked={requestType === t.value}
                  onChange={() => setRequestType(t.value)}
                  disabled={busy}
                />
                {t.label}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}

      {showUseCase ? (
        <label className="block text-sm">
          <span className="text-ds-text-muted">Use case / what you want to create</span>
          <textarea
            className={`${fieldClass} min-h-[100px]`}
            value={useCase}
            onChange={(ev) => setUseCase(ev.target.value)}
            required
            minLength={10}
            maxLength={500}
            placeholder="Music videos, ads, brand films, education content…"
            disabled={busy}
          />
        </label>
      ) : null}

      <label className="block text-sm">
        <span className="text-ds-text-muted">
          {messageLabel}
          {!messageRequired ? " (optional)" : ""}
        </span>
        <textarea
          className={`${fieldClass} min-h-[120px]`}
          value={message}
          onChange={(ev) => setMessage(ev.target.value)}
          required={messageRequired}
          minLength={messageRequired ? Math.max(1, messageMinLength) : undefined}
          maxLength={4000}
          placeholder={messagePlaceholder}
          disabled={busy}
        />
      </label>

      {requireTerms ? (
        <div className="space-y-2 text-sm text-ds-text-muted">
          <label className="flex items-start gap-2">
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
              </Link>
              .
            </span>
          </label>
          <label className="flex items-start gap-2">
            <input
              type="checkbox"
              className="mt-1"
              checked={acceptPrivacy}
              onChange={(ev) => setAcceptPrivacy(ev.target.checked)}
              disabled={busy}
              required
            />
            <span>
              I accept the{" "}
              <Link href="/privacy" className="text-ds-accent-lavender underline-offset-2 hover:underline">
                Privacy Policy
              </Link>
              .
            </span>
          </label>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <Button type="submit" variant="primary" disabled={busy}>
          {busy ? "Sending…" : submitLabel}
        </Button>
        <a
          href={`mailto:${SITE_SUPPORT_EMAIL}`}
          className="rtas-btn-ghost rtas-ui-btn"
        >
          Or email {SITE_SUPPORT_EMAIL}
        </a>
      </div>
    </form>
  );
}
