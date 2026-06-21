"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { BrandLockup } from "@/components/BrandLockup";
import { AuthFlowGuard } from "./AuthFlowGuard";

const DEV_VERIFY_KEY = "rtas_dev_verify_url";

type EmailConfig = {
  realInboxDelivery?: boolean;
  linkOnlyConfirmation?: boolean;
  smtpNeedsAppPassword?: boolean;
};

export function CheckEmailClient() {
  const searchParams = useSearchParams();
  const resendEmail = searchParams.get("email")?.trim() ?? "";
  const maskedEmail =
    searchParams.get("masked")?.trim() ||
    (resendEmail
      ? resendEmail.replace(/^(.{2}).*(@.*)$/, "$1***$2")
      : "your email");

  const [busy, setBusy] = useState(false);
  const [loadingLink, setLoadingLink] = useState(true);
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
        setError(data.error ?? "Could not prepare confirmation link.");
        return;
      }

      if (data.devVerificationUrl) {
        setDevVerificationUrl(data.devVerificationUrl);
        sessionStorage.setItem(DEV_VERIFY_KEY, data.devVerificationUrl);
      }

      if (showSuccessNotice) {
        setNotice(
          data.realInboxDelivery
            ? `Email sent to ${data.email ?? maskedEmail}. Check inbox and spam.`
            : "Confirmation link is ready below."
        );
      }
    } catch {
      setError("Could not prepare confirmation link.");
    } finally {
      setBusy(false);
      setLoadingLink(false);
    }
  }

  useEffect(() => {
    const stored = sessionStorage.getItem(DEV_VERIFY_KEY);
    if (stored) setDevVerificationUrl(stored);

    void fetch("/api/auth/email-config")
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: EmailConfig | null) => {
        setEmailConfig(cfg);
        if (cfg?.realInboxDelivery) {
          setLoadingLink(false);
          if (!stored) void loadVerificationLink(false);
          return;
        }
        if (cfg?.linkOnlyConfirmation) {
          setLoadingLink(false);
          if (!stored) void loadVerificationLink(false);
          return;
        }
        void loadVerificationLink(false);
      })
      .catch(() => {
        setEmailConfig({ realInboxDelivery: false, smtpNeedsAppPassword: true });
        void loadVerificationLink(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resendEmail]);

  const realInboxDelivery = emailConfig?.realInboxDelivery === true;
  const linkOnlyConfirmation = emailConfig?.linkOnlyConfirmation === true;
  const smtpNeedsAppPassword =
    emailConfig?.smtpNeedsAppPassword === true && !linkOnlyConfirmation;

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

        {smtpNeedsAppPassword && (
          <p className="auth-error" role="alert">
            <strong>Gmail email abhi send nahi ho rahi.</strong>{" "}
            <code>apps/web/.env.local</code> mein <code>SMTP_PASS=</code> ke baad
            Gmail App Password lagayein, phir server restart karein. Tab tak neeche wale
            button se account confirm karein.
          </p>
        )}

        {realInboxDelivery ? (
          <div className="auth-success" role="status">
            <p>
              Confirmation email bhej di gayi hai: <strong>{maskedEmail}</strong>
            </p>
            <p>
              Gmail inbox aur <strong>Spam</strong> folder check karein, phir{" "}
              <strong>Confirm my account</strong> par click karein.
            </p>
            <p>
              Confirm ke baad{" "}
              <Link href="/auth/login?callbackUrl=%2Fstudio">Sign in</Link> karein.
            </p>
          </div>
        ) : linkOnlyConfirmation ? (
          <div className="auth-success" role="status">
            <p>
              Aapka account tayar hai. Neeche <strong>Sign in now</strong> par
              click karke studio mein enter ho jayein.
            </p>
            <p className="auth-notice">
              Email inbox setup baad mein add ho sakta hai — abhi direct sign in
              use karein.
            </p>
          </div>
        ) : (
          <div className="auth-notice" role="status">
            <p>
              <strong>Abhi real email Gmail tak nahi ja rahi</strong> — SMTP
              password set nahi hai. Neeche <strong>Confirm my account now</strong>{" "}
              button use karein.
            </p>
          </div>
        )}

        {error && (
          <p className="auth-error" role="alert">
            {error}
          </p>
        )}

        {notice && (
          <p className="auth-notice" role="status">
            {notice}
          </p>
        )}

        {loadingLink && !devVerificationUrl && (
          <p className="auth-loading">Preparing confirmation link…</p>
        )}

        {devVerificationUrl && !linkOnlyConfirmation && (
          <>
            <a
              href={devVerificationUrl}
              className="btn-primary auth-submit auth-confirm-link-btn"
            >
              Confirm my account now
            </a>
            <p className="auth-dev-link">
              Link copy karein:{" "}
              <a href={devVerificationUrl}>{devVerificationUrl}</a>
            </p>
          </>
        )}

        {linkOnlyConfirmation && (
          <Link
            href="/auth/login?callbackUrl=%2Fstudio"
            className="btn-primary auth-submit auth-confirm-link-btn"
          >
            Sign in now
          </Link>
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
