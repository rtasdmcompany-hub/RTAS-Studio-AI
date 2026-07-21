"use client";

import { useState } from "react";
import Link from "next/link";
import { BrandLockup } from "@/components/BrandLockup";
import { AuthFlowGuard } from "./AuthFlowGuard";
import { Alert, Button, ButtonLink, Field, Input } from "@rtas/ui";

export function ForgotPasswordClient() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [devResetUrl, setDevResetUrl] = useState<string | null>(null);
  const [maskedEmail, setMaskedEmail] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    setDevResetUrl(null);

    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = (await res.json()) as {
        error?: string;
        message?: string;
        email?: string;
        devResetUrl?: string;
        emailSent?: boolean;
      };

      if (!res.ok) {
        setError(data.error ?? "Could not send password reset email.");
        return;
      }

      setMaskedEmail(data.email ?? email.replace(/^(.{2}).*(@.*)$/, "$1***$2"));
      setNotice(
        data.message ??
          "If an account with this email exists, we sent a password reset link."
      );
      if (data.devResetUrl) setDevResetUrl(data.devResetUrl);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <AuthFlowGuard mode="forgot-password" />
      <div className="auth-card">
        <div className="auth-card-header auth-card-header--lockup">
          <BrandLockup logoVariant="icon" logoSize={72} className="auth-brand-lockup" />
          <h1>Forgot password?</h1>
          <p>
            Enter your email and we&apos;ll send you a link to reset your password.
          </p>
        </div>

        {error && <Alert variant="error" message={error} />}
        {notice && <Alert variant="success" message={notice} />}

        {!notice ? (
          <form className="auth-form" onSubmit={handleSubmit}>
            <Field id="forgot-email" label="Email" required className="auth-field">
              <Input
                id="forgot-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </Field>

            <Button
              type="submit"
              variant="primary"
              className="auth-submit"
              disabled={busy}
              loading={busy}
              loadingLabel="Sending reset link…"
            >
              Send reset link
            </Button>
          </form>
        ) : (
          <>
            {devResetUrl && (
              <>
                <ButtonLink
                  href={devResetUrl}
                  variant="primary"
                  className="auth-submit auth-confirm-link-btn"
                >
                  Reset password now
                </ButtonLink>
                <p className="auth-dev-link">
                  Copy link: <a href={devResetUrl}>{devResetUrl}</a>
                </p>
              </>
            )}
            {maskedEmail && (
              <p className="auth-switch">
                Didn&apos;t get it? Check spam or try again with{" "}
                <strong>{maskedEmail}</strong>.
              </p>
            )}
            <Button
              type="button"
              variant="ghost"
              className="auth-submit"
              disabled={busy}
              loading={busy}
              onClick={() => {
                setNotice(null);
                setDevResetUrl(null);
              }}
            >
              Try another email
            </Button>
          </>
        )}

        <p className="auth-switch">
          Remember your password?{" "}
          <Link href="/auth/login">Back to sign in</Link>
        </p>

        <Link href="/" className="auth-home-link">
          ← Back to home
        </Link>
      </div>
    </>
  );
}
