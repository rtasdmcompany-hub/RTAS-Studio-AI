"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { BrandLockup } from "@/components/BrandLockup";
import { AuthLinkSkeleton } from "@/components/ui/skeletons";
import { Alert, Button, ButtonLink } from "@rtas/ui";
import { AuthFlowGuard } from "./AuthFlowGuard";

const DEV_VERIFY_KEY = "rtas_dev_verify_url";
const EMAIL_SENT_KEY = "rtas_email_sent";

type EmailConfig = {
  realInboxDelivery?: boolean;
  mode?: string;
  resendSandboxFrom?: boolean;
  smtpNeedsAppPassword?: boolean;
};

export function CheckEmailClient() {
  const searchParams = useSearchParams();
  const resendEmail = searchParams.get("email")?.trim() ?? "";
  const justSignedUp = searchParams.get("sent") === "1";
  const maskedEmail =
    searchParams.get("masked")?.trim() ||
    (resendEmail
      ? resendEmail.replace(/^(.{2}).*(@.*)$/, "$1***$2")
      : "your email");

  const [busy, setBusy] = useState(false);
  const [loadingLink, setLoadingLink] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [devVerificationUrl, setDevVerificationUrl] = useState<string | null>(null);
  const [emailConfig, setEmailConfig] = useState<EmailConfig | null>(null);
  const [inboxEmailSent, setInboxEmailSent] = useState<boolean | null>(null);

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
        emailSent?: boolean;
        realInboxDelivery?: boolean;
        deliveryError?: string;
      };

      if (!res.ok) {
        setError(data.error ?? "Could not send confirmation email.");
        return;
      }

      const sentToInbox = data.emailSent === true || data.realInboxDelivery === true;
      setInboxEmailSent(sentToInbox);
      sessionStorage.setItem(EMAIL_SENT_KEY, sentToInbox ? "1" : "0");

      if (data.devVerificationUrl) {
        setDevVerificationUrl(data.devVerificationUrl);
        sessionStorage.setItem(DEV_VERIFY_KEY, data.devVerificationUrl);
      }

      if (showSuccessNotice) {
        if (sentToInbox) {
          setNotice(
            `Confirmation email sent to ${data.email ?? maskedEmail}. Check your inbox and spam folder.`
          );
        } else {
          setNotice(
            data.deliveryError
              ? "Your account is ready. Use Confirm my account now below to activate it."
              : "Your confirmation link is ready below."
          );
        }
      }
    } catch {
      setError("Could not send confirmation email.");
    } finally {
      setBusy(false);
      setLoadingLink(false);
    }
  }

  useEffect(() => {
    const storedUrl = sessionStorage.getItem(DEV_VERIFY_KEY);
    if (storedUrl) setDevVerificationUrl(storedUrl);

    const storedSent = sessionStorage.getItem(EMAIL_SENT_KEY);
    if (storedSent === "1") setInboxEmailSent(true);
    else if (storedSent === "0") setInboxEmailSent(false);

    void fetch("/api/auth/email-config")
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: EmailConfig | null) => {
        setEmailConfig(cfg);

        if (justSignedUp) {
          if (storedSent === "1") {
            setNotice(
              `We sent a confirmation email to ${maskedEmail}. Open the email, click Confirm my account, then sign in.`
            );
          } else if (storedUrl) {
            setNotice(
              "Your account is ready. Click Confirm my account now below, then sign in."
            );
          } else if (cfg?.realInboxDelivery) {
            setNotice(
              `We sent a confirmation email to ${maskedEmail}. Check your inbox and spam folder.`
            );
          }
          return;
        }

        if (cfg?.mode === "dev-file" || !cfg?.realInboxDelivery) {
          void loadVerificationLink(false);
          return;
        }

        setLoadingLink(false);
      })
      .catch(() => {
        setEmailConfig({ realInboxDelivery: false, smtpNeedsAppPassword: true });
        if (!justSignedUp) void loadVerificationLink(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resendEmail, justSignedUp, maskedEmail]);

  const realInboxDelivery = emailConfig?.realInboxDelivery === true;
  const devFileMode = emailConfig?.mode === "dev-file";
  const resendSandboxFrom = emailConfig?.resendSandboxFrom === true;
  const smtpNeedsAppPassword = emailConfig?.smtpNeedsAppPassword === true;
  const showOnPageConfirm = Boolean(devVerificationUrl);
  const emailWasSentToInbox = inboxEmailSent === true;

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
          <Alert variant="success" message={notice} />
        )}

        {realInboxDelivery && emailWasSentToInbox && !notice && (
          <Alert
            variant="success"
            message={
              <>
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
              </>
            }
          />
        )}

        {resendSandboxFrom && (
          <Alert
            variant="info"
            message={
              <>
                Inbox email is not active yet because the sending domain is not verified in
                Resend. Use <strong>Confirm my account now</strong> below to activate your account.
              </>
            }
          />
        )}

        {devFileMode && (
          <Alert
            variant="info"
            message={
              <>
                Email delivery is in local development mode. Use the confirmation link below
                to verify your account, then sign in.
              </>
            }
          />
        )}

        {smtpNeedsAppPassword && (
          <Alert
            variant="error"
            message={
              <>
                SMTP is not configured in <code>apps/web/.env.local</code>. Add{" "}
                <code>SMTP_PASS</code> for real email delivery, or use the confirmation link
                below.
              </>
            }
          />
        )}

        {error && (
          <Alert variant="error" message={error} />
        )}

        {loadingLink && !devVerificationUrl && <AuthLinkSkeleton />}

        {showOnPageConfirm && (
          <>
            <ButtonLink
              href={devVerificationUrl!}
              variant="primary"
              className="auth-submit auth-confirm-link-btn"
            >
              Confirm my account now
            </ButtonLink>
            {!resendSandboxFrom && !realInboxDelivery && (
              <p className="auth-dev-link">
                Copy link: <a href={devVerificationUrl!}>{devVerificationUrl}</a>
              </p>
            )}
          </>
        )}

        <Button
          type="button"
          variant="ghost"
          className="auth-submit"
          disabled={busy || !resendEmail}
          loading={busy}
          loadingLabel="Working…"
          onClick={() => void loadVerificationLink(true)}
        >
          {realInboxDelivery
            ? "Resend confirmation email"
            : "Refresh confirmation link"}
        </Button>

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

export function storeEmailSentToInbox(sent: boolean) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(EMAIL_SENT_KEY, sent ? "1" : "0");
}

export function clearDevVerificationUrl() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(DEV_VERIFY_KEY);
  sessionStorage.removeItem(EMAIL_SENT_KEY);
}
