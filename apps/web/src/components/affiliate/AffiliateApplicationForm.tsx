"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert, Button } from "@rtas/ui";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";

const fieldClass =
  "mt-1 w-full rounded-lg border border-ds-border bg-ds-surface px-3 py-2 text-ds-text";

const AUDIENCE_SIZES = [
  { value: "under_1k", label: "Under 1,000" },
  { value: "1k_10k", label: "1,000 – 10,000" },
  { value: "10k_50k", label: "10,000 – 50,000" },
  { value: "50k_250k", label: "50,000 – 250,000" },
  { value: "250k_plus", label: "250,000+" },
] as const;

const PAYOUT_PREFS = [
  { value: "paypal", label: "PayPal (when payouts enable)" },
  { value: "wise", label: "Wise (when payouts enable)" },
  { value: "bank", label: "Bank transfer (when payouts enable)" },
  { value: "undecided", label: "Undecided" },
] as const;

export function AffiliateApplicationForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [website, setWebsite] = useState("");
  const [audienceSize, setAudienceSize] = useState("");
  const [channels, setChannels] = useState("");
  const [audienceDescription, setAudienceDescription] = useState("");
  const [promotionPlan, setPromotionPlan] = useState("");
  const [payoutPreference, setPayoutPreference] = useState("");
  const [taxCountry, setTaxCountry] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptProgramRules, setAcceptProgramRules] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!acceptTerms || !acceptProgramRules) {
      setError("Please accept the terms and affiliate program rules to continue.");
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/affiliate/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email,
          company,
          website,
          audienceSize,
          channels,
          audienceDescription,
          promotionPlan,
          payoutPreference,
          taxCountry,
          acceptTerms,
          acceptProgramRules,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        ok?: boolean;
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
          `Thanks — your application was received. We will reply to ${email}. Commission payouts are not live until RTAS enables them.`
      );
      setName("");
      setEmail("");
      setCompany("");
      setWebsite("");
      setAudienceSize("");
      setChannels("");
      setAudienceDescription("");
      setPromotionPlan("");
      setPayoutPreference("");
      setTaxCountry("");
      setAcceptTerms(false);
      setAcceptProgramRules(false);
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

      <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100/90">
        Applications are open for review. Commission payouts are{" "}
        <strong>not live</strong> until RTAS configures attribution and payment rails.
        Do not treat this form as a live earnings offer.
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

      <label className="block text-sm">
        <span className="text-ds-text-muted">Company / brand (optional)</span>
        <input
          className={fieldClass}
          value={company}
          onChange={(ev) => setCompany(ev.target.value)}
          maxLength={160}
          autoComplete="organization"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Primary website or profile URL (optional)</span>
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
        <span className="text-ds-text-muted">Audience size (approx.)</span>
        <select
          className={fieldClass}
          value={audienceSize}
          onChange={(ev) => setAudienceSize(ev.target.value)}
          required
          disabled={busy}
        >
          <option value="">Select…</option>
          {AUDIENCE_SIZES.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Channels (YouTube, TikTok, newsletter, etc.)</span>
        <input
          className={fieldClass}
          value={channels}
          onChange={(ev) => setChannels(ev.target.value)}
          required
          minLength={3}
          maxLength={240}
          placeholder="e.g. YouTube tutorials, LinkedIn newsletter"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Audience description (optional)</span>
        <textarea
          className={`${fieldClass} min-h-[80px]`}
          value={audienceDescription}
          onChange={(ev) => setAudienceDescription(ev.target.value)}
          maxLength={1000}
          placeholder="Who follows you? Creators, agencies, marketers…"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">How you plan to promote RTAS Studio AI</span>
        <textarea
          className={`${fieldClass} min-h-[120px]`}
          value={promotionPlan}
          onChange={(ev) => setPromotionPlan(ev.target.value)}
          required
          minLength={40}
          maxLength={4000}
          placeholder="Content formats, frequency, and how you will disclose the affiliate relationship…"
          disabled={busy}
        />
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Preferred payout method (when enabled)</span>
        <select
          className={fieldClass}
          value={payoutPreference}
          onChange={(ev) => setPayoutPreference(ev.target.value)}
          required
          disabled={busy}
        >
          <option value="">Select…</option>
          {PAYOUT_PREFS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm">
        <span className="text-ds-text-muted">Tax / residence country</span>
        <input
          className={fieldClass}
          value={taxCountry}
          onChange={(ev) => setTaxCountry(ev.target.value)}
          required
          minLength={2}
          maxLength={80}
          autoComplete="country-name"
          disabled={busy}
        />
      </label>

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
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-ds-accent-lavender underline-offset-2 hover:underline">
              Privacy Policy
            </Link>
            .
          </span>
        </label>
        <label className="flex items-start gap-2">
          <input
            type="checkbox"
            className="mt-1"
            checked={acceptProgramRules}
            onChange={(ev) => setAcceptProgramRules(ev.target.checked)}
            disabled={busy}
            required
          />
          <span>
            I understand commission rates are placeholders until confirmed in writing, payouts are
            not live yet, and I will not promote unauthorized likeness / deepfake use cases.
          </span>
        </label>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button type="submit" variant="primary" disabled={busy}>
          {busy ? "Submitting…" : "Apply to affiliate program"}
        </Button>
        <a href={`mailto:${SITE_SUPPORT_EMAIL}`} className="rtas-btn-ghost rtas-ui-btn">
          Or email {SITE_SUPPORT_EMAIL}
        </a>
      </div>
    </form>
  );
}
