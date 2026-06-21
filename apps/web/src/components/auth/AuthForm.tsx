"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { signIn, signOut } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { PRODUCT_NAME } from "@rtas/shared";
import { GoogleSignInButton } from "./GoogleSignInButton";
import { BrandLockup } from "@/components/BrandLockup";
import { storeDevVerificationUrl, storeEmailSentToInbox } from "./CheckEmailClient";

type Mode = "login" | "signup";

function mapAuthError(code: string | null): string {
  if (!code) return "Authentication failed. Please try again.";
  switch (code) {
    case "OAuthAccountNotLinked":
      return "This email is registered with a password. Sign in with email instead.";
    case "invalid_verification_link":
      return "Invalid confirmation link. Request a new confirmation email.";
    case "Configuration":
    case "OAuthSignin":
    case "OAuthCallback":
    case "google":
      return (
        "Google sign-in failed. Check that Google OAuth redirect URI and JavaScript origin " +
        "match your live site URL in Google Cloud Console, and that NEXTAUTH_URL is set on Vercel."
      );
    default:
      if (code.includes("expired") || code.includes("invalid")) return code;
      return `Authentication failed (${code}). Check Google Cloud OAuth settings and restart the dev server.`;
  }
}

type Props = {
  mode: Mode;
};

export function AuthForm({ mode }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/studio";
  const authError = searchParams.get("error");
  const verified = searchParams.get("verified") === "1";
  const verifiedEmail = searchParams.get("email");
  const passwordLinked = searchParams.get("passwordLinked") === "1";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [googleAuthEnabled, setGoogleAuthEnabled] = useState<boolean | null>(null);
  const [simulationMode, setSimulationMode] = useState<boolean | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [signupSentModal, setSignupSentModal] = useState<{
    email: string;
    masked: string;
    emailSent: boolean;
    devVerificationUrl?: string;
  } | null>(null);

  useEffect(() => {
    if (verified) {
      setSuccess(
        verifiedEmail
          ? `Email confirmed for ${verifiedEmail}. Sign in below to continue.`
          : "Email confirmed. Sign in below to continue."
      );
    } else if (passwordLinked) {
      setSuccess("Password saved. Sign in with your email and password.");
    }
  }, [verified, verifiedEmail, passwordLinked]);

  useEffect(() => {
    void fetch("/api/auth/config")
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: { googleAuthEnabled?: boolean; simulationMode?: boolean } | null) => {
        if (!cfg) return;
        setGoogleAuthEnabled(Boolean(cfg.googleAuthEnabled));
        setSimulationMode(Boolean(cfg.simulationMode));
      })
      .catch(() => {
        /* keep safe defaults */
      });
  }, []);

  const isSignup = mode === "signup";
  const title = isSignup ? "Create your account" : "Welcome back";
  const subtitle = isSignup
    ? `Join ${PRODUCT_NAME} and start creating AI videos.`
    : `Sign in to continue to your ${PRODUCT_NAME} workspace.`;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setError(null);
    setSuccess(null);
    setStatusMessage(null);
    setBusy(true);

    try {
      if (isSignup) {
        setStatusMessage("Creating your account…");
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 90_000);
        let res: Response;
        try {
          res = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, name }),
            signal: controller.signal,
          });
        } finally {
          window.clearTimeout(timeout);
        }

        let data: {
          error?: string;
          linkedGoogleAccount?: boolean;
          needsEmailVerification?: boolean;
          email?: string;
          emailSent?: boolean;
          realInboxDelivery?: boolean;
          devVerificationUrl?: string;
        };
        try {
          data = (await res.json()) as typeof data;
        } catch {
          setError("Sign up failed. Please try again.");
          return;
        }

        if (!res.ok) {
          setError(data.error ?? "Sign up failed.");
          return;
        }

        await signOut({ redirect: false });
        const emailSent = data.emailSent === true || data.realInboxDelivery === true;
        storeEmailSentToInbox(emailSent);
        storeDevVerificationUrl(data.devVerificationUrl);

        const masked = data.email ?? email.replace(/^(.{2}).*(@.*)$/, "$1***$2");
        setSignupSentModal({
          email,
          masked,
          emailSent,
          devVerificationUrl: data.devVerificationUrl,
        });
        return;
      }

      setStatusMessage("Signing you in…");

      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl,
      });

      if (result?.error) {
        const checkRes = await fetch("/api/auth/check-verification", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }).catch(() => null);

        if (checkRes?.ok) {
          const check = (await checkRes.json()) as { unverified?: boolean };
          if (check.unverified) {
            router.replace(
              `/auth/check-email?email=${encodeURIComponent(email)}&masked=${encodeURIComponent(email.replace(/^(.{2}).*(@.*)$/, "$1***$2"))}`
            );
            return;
          }
        }

        setError("Invalid email or password.");
        return;
      }

      router.push(result?.url ?? callbackUrl);
      router.refresh();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setError(
          "Sign up is taking too long. Check your connection and try again, or use Continue with Google."
        );
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setBusy(false);
      setStatusMessage(null);
    }
  }

  function closeSignupSentModal() {
    if (!signupSentModal) return;
    const masked = encodeURIComponent(signupSentModal.masked);
    router.push(
      `/auth/check-email?email=${encodeURIComponent(signupSentModal.email)}&masked=${masked}&sent=1`
    );
    setSignupSentModal(null);
  }

  return (
    <>
      {signupSentModal && (
        <div className="auth-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="signup-sent-title">
          <div className="auth-modal">
            <h2 id="signup-sent-title">
              {signupSentModal.emailSent ? "Check your email" : "Confirm your account"}
            </h2>
            {signupSentModal.emailSent ? (
              <>
                <p>
                  We sent a confirmation email to <strong>{signupSentModal.masked}</strong>.
                </p>
                <p>
                  Open the email, click <strong>Confirm my account</strong>, then sign in.
                  You cannot access the studio until your email is verified.
                </p>
              </>
            ) : (
              <>
                <p>
                  Your account for <strong>{signupSentModal.masked}</strong> was created, but
                  we could not deliver email to your inbox yet.
                </p>
                <p>
                  On the next screen, click <strong>Confirm my account now</strong> to verify
                  your email, then sign in.
                </p>
              </>
            )}
            <button type="button" className="btn-primary auth-submit" onClick={closeSignupSentModal}>
              Got it
            </button>
          </div>
        </div>
      )}

      <div className="auth-card">
      <div className="auth-card-header auth-card-header--lockup">
        <BrandLockup logoVariant="icon" logoSize={72} className="auth-brand-lockup" />
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      {(error || authError) && (
        <p className="auth-error" role="alert">
          {error ?? mapAuthError(authError)}
        </p>
      )}

      {success && (
        <p className="auth-success" role="status">
          {success}
        </p>
      )}

      {googleAuthEnabled === true && (
        <>
          <GoogleSignInButton callbackUrl={callbackUrl} />
          <div className="auth-divider">
            <span>or</span>
          </div>
        </>
      )}

      {simulationMode === true && (
        <p className="auth-simulation-note">
          Cloud AI keys are not configured on this deployment — studio runs in
          simulation mode with demo previews until you add <code>FAL_KEY</code>{" "}
          (or <code>REPLICATE_API_TOKEN</code>) to your hosting environment
          variables.
        </p>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        {isSignup && (
          <label className="auth-field">
            <span>Full name</span>
            <input
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              required
            />
          </label>
        )}

        <label className="auth-field">
          <span>Email</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </label>

        <label className="auth-field">
          <span>Password</span>
          <input
            type="password"
            autoComplete={isSignup ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={isSignup ? "At least 8 characters" : "Your password"}
            minLength={isSignup ? 8 : 1}
            required
          />
        </label>

        <button type="submit" className="btn-primary auth-submit" disabled={busy}>
          {busy
            ? statusMessage ?? (isSignup ? "Creating account…" : "Signing in…")
            : isSignup
              ? "Create account"
              : "Sign in"}
        </button>
      </form>

      <p className="auth-switch">
        {isSignup ? (
          <>
            Already have an account?{" "}
            <Link href={`/auth/login?callbackUrl=${encodeURIComponent(callbackUrl)}`}>
              Sign in
            </Link>
          </>
        ) : (
          <>
            New to {PRODUCT_NAME}?{" "}
            <Link href={`/auth/signup?callbackUrl=${encodeURIComponent(callbackUrl)}`}>
              Sign up
            </Link>
          </>
        )}
      </p>

      <Link href="/" className="auth-home-link">
        ← Back to home
      </Link>
    </div>
    </>
  );
}
