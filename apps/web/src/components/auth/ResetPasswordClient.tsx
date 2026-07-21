"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { BrandLockup } from "@/components/BrandLockup";
import { AuthFlowGuard } from "./AuthFlowGuard";
import { Alert, Button, Field, Input } from "@rtas/ui";

export function ResetPasswordClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setError(null);

    if (!token) {
      setError("Invalid or missing reset link. Request a new password reset.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const data = (await res.json()) as { error?: string; email?: string };

      if (!res.ok) {
        setError(data.error ?? "Could not reset password.");
        return;
      }

      const emailParam = data.email
        ? `&email=${encodeURIComponent(data.email)}`
        : "";
      router.replace(`/auth/login?passwordReset=1${emailParam}`);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <AuthFlowGuard mode="reset-password" />
      <div className="auth-card">
        <div className="auth-card-header auth-card-header--lockup">
          <BrandLockup logoVariant="icon" logoSize={72} className="auth-brand-lockup" />
          <h1>Choose a new password</h1>
          <p>Enter a new password for your account.</p>
        </div>

        {!token && (
          <Alert
            variant="error"
            message={
              <>
                This reset link is invalid or missing.{" "}
                <Link href="/auth/forgot-password">Request a new reset link</Link>.
              </>
            }
          />
        )}

        {error && <Alert variant="error" message={error} />}

        <form className="auth-form" onSubmit={handleSubmit}>
          <Field id="reset-password" label="New password" required className="auth-field">
            <Input
              id="reset-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              minLength={8}
              required
              disabled={!token}
            />
          </Field>

          <Field
            id="reset-confirm"
            label="Confirm password"
            required
            className="auth-field"
          >
            <Input
              id="reset-confirm"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat your password"
              minLength={8}
              required
              disabled={!token}
            />
          </Field>

          <Button
            type="submit"
            variant="primary"
            className="auth-submit"
            disabled={busy || !token}
            loading={busy}
            loadingLabel="Updating password…"
          >
            Update password
          </Button>
        </form>

        <p className="auth-switch">
          <Link href="/auth/forgot-password">Request a new reset link</Link>
          {" · "}
          <Link href="/auth/login">Back to sign in</Link>
        </p>

        <Link href="/" className="auth-home-link">
          ← Back to home
        </Link>
      </div>
    </>
  );
}
