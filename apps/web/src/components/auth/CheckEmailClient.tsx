"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { BrandLockup } from "@/components/BrandLockup";
import { AuthFlowGuard } from "./AuthFlowGuard";

const DEV_VERIFY_KEY = "rtas_dev_verify_url";

type EmailConfig = {
  realInboxDelivery?: boolean;
  mode?: string;
  smtpNeedsAppPassword?: boolean;
};

export function CheckEmailClient() {
  const searchParams = useSearchParams();
  const resendEmail = searchParams.get("email")?.trim() ?? "";
  const justSent = searchParams.get("sent") === "1";
  const maskedEmail =
    searchParams.get("masked")?.trim() ||
    (resendEmail
      ? resendEmail.replace(/^(.{2}).*(@.*)$/, "$1***$2")
      : "your email");

  const [busy, setBusy] = useState(false);
  const [loadingLink, setLoadingLink] = useState(!justSent);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [devVerificationUrl, setDevVerificationUrl] = useState<string | null>(null);
  const [emailConfig, setEmailConfig] = useState<EmailConfig | null>(null);

  async function loadVerificationLink(showSuccessNotice = false) {
    if (!resendEmail) {
      setLoadingLink(false);
      return;
    }

    setBusy(true);
    setError(null);
    if (!showSuccessNotice) setNotice(null);

    try {
      const res = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: resendEmail }),
      });
      const data = (await res.json()) as {
        error?: string;
        message?: string;
        email?: string;
        devVerificationUrl?: string;
        realInboxDelivery?: boolean;
      };

      if (!res.ok) {
        setError(data.error ?? "Could not send confirmation email.");
        return;
      }

      if (data.devVerificationUrl) {
        setDevVerificationUrl(data.devVerificationUrl);
        sessionStorage.setItem(DEV_VERIFY_KEY, data.devVerificationUrl);
      }

      if (showSuccessNotice) {
        setNotice(
          data.realInboxDelivery
            ? `Confirmation email sent to ${data.email ?? maskedEmail}. Check your inbox and spam folder.`
            : "Confirmation link is ready below."
        );
      }
    } catch {
      setError("Could not send confirmation email.");
    } finally {
      setBusy(false);
      setLoadingLink(false);
    }
  }

  useEffect(() => {
    const stored = sessionStorage.getItem(DEV_VERIFY_KEY);
    if (stored) setDevVerificationUrl(stored);

    if (justSent) {
      setNotice(
        `We sent a confirmation email to ${maskedEmail}. Open the email, click Confirm my account, then sign in. You cannot access the studio until your email is verified.`
      );
      setLoadingLink(false);
    }

    void fetch("/api/auth/email-config")
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: EmailConfig | null) => {
        setEmailConfig(cfg);
        if (justSent) return;
        if (cfg?.mode === "dev-file") {
          void loadVerificationLink(false);
          return;
        }
        setLoadingLink(false);
      })
      .catch(() => {
        setEmailConfig({ realInboxDelivery: false, smtpNeedsAppPassword: true });
        if (!justSent) void loadVerificationLink(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resendEmail, justSent, maskedEmail]);

  const realInboxDelivery = emailConfig?.realInboxDelivery === true;
  const devFileMode = emailConfig?.mode === "dev-file";
  const smtpNeedsAppPassword = emailConfig?.smtpNeedsAppPassword === true;

  return (
    <>
      <AuthFlowGuard mode="check-email" />
      <div className="auth-card">
        <div className="auth-card-header auth-card-header--lockup">
          <BrandLockup logoVariant="icon" logoSize={72} className="auth-brand-lockup" />
          <h1>Confirm your email</h1>
          <p>
            Account for <strong>{maskedEmail}</strong> is waiting for confirmation.
          </p>
        </div>

        {notice && (
          <div className="auth-success auth-confirmation-banner" role="status">
            <p>{notice}</p>
          </div>
        )}

        {realInboxDelivery && !notice && (
          <div className="auth-success" role="status">
            <p>
              We sent a confirmation email to <strong>{maskedEmail}</strong>.
            </p>
            <p>
              Check your inbox and spam folder, then click <strong>Confirm my account</strong>.
            </p>
            <p>
              After confirming,{" "}
              <Link href="/auth/login?callbackUrl=%2Fstudio">sign in</Link> to open Studio.
            </p>
          </div>
        )}

        {devFileMode && (
          <div className="auth-notice" role="status">
            <p>
              Email delivery is in local development mode. Use the confirmation link below
              to verify your account, then sign in.
            </p>
          </div>
        )}

        {smtpNeedsAppPassword && (
          <p className="auth-error" role="alert">
            SMTP is not configured in <code>apps/web/.env.local</code>. Add{" "}
            <code>SMTP_PASS</code> for real email delivery, or use the development link
            below to confirm locally.
          </p>
        )}

        {error && (
          <p className="auth-error" role="alert">
            {error}
          </p>
        )}

        {loadingLink && !devVerificationUrl && devFileMode && (
          <p className="auth-loading">Preparing confirmation link…</p>
        )}

        {devVerificationUrl && devFileMode && (
          <>
            <a
              href={devVerificationUrl}
              className="btn-primary auth-submit auth-confirm-link-btn"
            >
              Confirm my account now
            </a>
            <p className="auth-dev-link">
              Copy link: <a href={devVerificationUrl}>{devVerificationUrl}</a>
            </p>
          </>
        )}

        <button
          type="button"
          className="btn-ghost auth-submit"
          disabled={busy || !resendEmail}
          onClick={() => void loadVerificationLink(true)}
        >
          {busy
            ? "Working…"
            : realInboxDelivery
              ? "Resend confirmation email"
              : "Refresh confirmation link"}
        </button>

        <p className="auth-switch">
          Already confirmed?{" "}
          <Link href="/auth/login?callbackUrl=%2Fstudio">Sign in</Link>
        </p>

        <Link href="/" className="auth-home-link">
          ← Back to home
        </Link>
      </div>
    </>
  );
}

export function storeDevVerificationUrl(url?: string) {
  if (typeof window === "undefined" || !url) return;
  sessionStorage.setItem(DEV_VERIFY_KEY, url);
}

export function clearDevVerificationUrl() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(DEV_VERIFY_KEY);
}
