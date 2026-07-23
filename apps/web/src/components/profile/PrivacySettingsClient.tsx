"use client";

import { useCallback, useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { Alert, Button, ButtonLink, Card } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import {
  DEFAULT_NECESSARY_ONLY,
  openCookiePreferences,
  readCookieConsent,
  writeCookieConsent,
  type CookieCategoryPrefs,
} from "@/lib/analytics";
import { SITE_PRIVACY_EMAIL } from "@/lib/site-links";

type SessionInfo = {
  strategy: string;
  note: string;
  current: {
    email: string | null;
    emailVerified: boolean;
    provider: string;
    hasPassword: boolean;
    lastLoginAt: string | null;
    twoFactorEnabled: boolean;
    twoFactorStatus: string;
  };
};

export function PrivacySettingsClient() {
  const { status } = useSession();
  const [cookiePrefs, setCookiePrefs] = useState<CookieCategoryPrefs | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [deleteNote, setDeleteNote] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const refreshCookies = useCallback(() => {
    setCookiePrefs(readCookieConsent());
  }, []);

  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch("/api/user/privacy/sessions");
      const json = (await res.json()) as SessionInfo & { ok?: boolean; error?: string };
      if (!res.ok || !json.ok) throw new Error(json.error ?? "Could not load session info.");
      setSessionInfo(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Session load failed.");
    }
  }, []);

  useEffect(() => {
    refreshCookies();
    if (status === "authenticated") void loadSessions();
  }, [status, refreshCookies, loadSessions]);

  async function downloadExport() {
    setBusy(true);
    setError(null);
    setOkMsg(null);
    try {
      const res = await fetch("/api/user/privacy/export");
      if (!res.ok) {
        const json = (await res.json().catch(() => ({}))) as { error?: string };
        throw new Error(json.error ?? "Export failed.");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rtas-personal-data-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setOkMsg("Personal data export downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setBusy(false);
    }
  }

  async function submitDeletion() {
    if (!deleteConfirm) {
      setError("Confirm that you want to request account deletion.");
      return;
    }
    setBusy(true);
    setError(null);
    setOkMsg(null);
    try {
      const res = await fetch("/api/user/privacy/deletion-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true, note: deleteNote }),
      });
      const json = (await res.json()) as {
        ok?: boolean;
        ticketNumber?: string;
        message?: string;
        error?: string;
      };
      if (!res.ok || !json.ok) throw new Error(json.error ?? "Request failed.");
      setOkMsg(
        `${json.message ?? "Request received."}${
          json.ticketNumber ? ` Ticket: ${json.ticketNumber}` : ""
        }`
      );
      setDeleteConfirm(false);
      setDeleteNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  }

  function saveCookieDraft(next: CookieCategoryPrefs) {
    writeCookieConsent(next);
    setCookiePrefs(next);
    setOkMsg("Cookie preferences saved.");
  }

  if (status === "unauthenticated") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection className="pt-8">
            <h1 className="font-display text-4xl text-ds-text">Privacy settings</h1>
            <p className="mt-3 text-ds-text-muted">
              Sign in to download your data, manage preferences, or request deletion.
            </p>
            <Link
              href="/auth/signin?callbackUrl=/profile/privacy"
              className="mt-6 inline-block text-ds-accent"
            >
              Sign in →
            </Link>
          </InnerPageSection>
        </InnerPageContainer>
      </MarketingLayout>
    );
  }

  const prefs = cookiePrefs ?? DEFAULT_NECESSARY_ONLY;

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="pt-8">
          <p className="rtas-eyebrow">Account</p>
          <h1 className="font-display text-4xl text-ds-text">Privacy settings</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Download personal data, manage cookie and email preferences, review session
            posture, or request account deletion. Rights also remain available via{" "}
            <a href={`mailto:${SITE_PRIVACY_EMAIL}`}>{SITE_PRIVACY_EMAIL}</a>.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <ButtonLink href="/profile" variant="ghost">
              Dashboard
            </ButtonLink>
            <ButtonLink href="/profile/notifications" variant="ghost">
              Email preferences
            </ButtonLink>
            <ButtonLink href="/security" variant="ghost">
              Security Center
            </ButtonLink>
          </div>
        </InnerPageSection>

        {error ? <Alert variant="error" message={error} /> : null}
        {okMsg ? <Alert variant="info" message={okMsg} /> : null}

        <Card className="space-y-3 p-5">
          <h2 className="text-xl text-zinc-100">Download personal data</h2>
          <p className="text-sm text-ds-text-muted">
            JSON export of account metadata, projects, generation jobs, tickets, and
            notification preferences. Password hashes and card numbers are never included.
          </p>
          <Button
            type="button"
            variant="lavender"
            disabled={busy}
            onClick={() => void downloadExport()}
          >
            Download my data
          </Button>
        </Card>

        <Card className="mt-4 space-y-3 p-5">
          <h2 className="text-xl text-zinc-100">Cookie preferences</h2>
          <p className="text-sm text-ds-text-muted">
            Necessary cookies stay on. Analytics and Marketing are optional and gate
            optional trackers before load.
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center justify-between gap-4 border-b border-white/5 py-2">
              <span>Necessary</span>
              <input type="checkbox" checked disabled readOnly />
            </li>
            <li className="flex items-center justify-between gap-4 border-b border-white/5 py-2">
              <span>Analytics</span>
              <input
                type="checkbox"
                checked={prefs.analytics}
                onChange={(e) =>
                  saveCookieDraft({
                    necessary: true,
                    analytics: e.target.checked,
                    marketing: prefs.marketing,
                  })
                }
              />
            </li>
            <li className="flex items-center justify-between gap-4 border-b border-white/5 py-2">
              <span>Marketing</span>
              <input
                type="checkbox"
                checked={prefs.marketing}
                onChange={(e) =>
                  saveCookieDraft({
                    necessary: true,
                    analytics: prefs.analytics,
                    marketing: e.target.checked,
                  })
                }
              />
            </li>
          </ul>
          <Button type="button" variant="ghost" onClick={() => openCookiePreferences()}>
            Open banner preference panel
          </Button>
        </Card>

        <Card className="mt-4 space-y-3 p-5">
          <h2 className="text-xl text-zinc-100">Active session</h2>
          {sessionInfo ? (
            <>
              <p className="text-sm text-ds-text-muted">{sessionInfo.note}</p>
              <dl className="grid gap-2 text-sm text-ds-text-muted md:grid-cols-2">
                <div>
                  <dt className="text-zinc-400">Email</dt>
                  <dd className="text-zinc-100">{sessionInfo.current.email ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-zinc-400">Provider</dt>
                  <dd className="text-zinc-100">{sessionInfo.current.provider}</dd>
                </div>
                <div>
                  <dt className="text-zinc-400">Email verified</dt>
                  <dd className="text-zinc-100">
                    {sessionInfo.current.emailVerified ? "Yes" : "No"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-400">Password on file</dt>
                  <dd className="text-zinc-100">
                    {sessionInfo.current.hasPassword ? "Yes" : "No (OAuth-only)"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-400">Last login</dt>
                  <dd className="text-zinc-100">
                    {sessionInfo.current.lastLoginAt
                      ? new Date(sessionInfo.current.lastLoginAt).toLocaleString()
                      : "Not recorded"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-400">Two-factor auth</dt>
                  <dd className="text-zinc-100">Roadmap (not implemented)</dd>
                </div>
              </dl>
              <div className="flex flex-wrap gap-3">
                {sessionInfo.current.hasPassword ? (
                  <ButtonLink href="/auth/forgot-password" variant="ghost">
                    Change password
                  </ButtonLink>
                ) : null}
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => void signOut({ callbackUrl: "/" })}
                >
                  Sign out this browser
                </Button>
              </div>
            </>
          ) : (
            <p className="text-sm text-ds-text-muted">Loading session…</p>
          )}
        </Card>

        <Card className="mt-4 space-y-3 p-5">
          <h2 className="text-xl text-zinc-100">Request account deletion</h2>
          <p className="text-sm text-ds-text-muted">
            Submits a high-priority privacy ticket for review. Deletion is not instant —
            we verify identity and retain records required for billing, fraud prevention,
            or law (typically up to statutory periods).
          </p>
          <textarea
            className="min-h-[88px] w-full rounded-lg border border-white/10 bg-black/20 p-3 text-sm text-zinc-100"
            placeholder="Optional note for our privacy team"
            value={deleteNote}
            onChange={(e) => setDeleteNote(e.target.value)}
            maxLength={2000}
          />
          <label className="flex items-start gap-2 text-sm text-ds-text-muted">
            <input
              type="checkbox"
              checked={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.checked)}
            />
            I understand this queues a deletion review and does not wipe my account
            immediately.
          </label>
          <Button
            type="button"
            variant="ghost"
            disabled={busy || !deleteConfirm}
            onClick={() => void submitDeletion()}
          >
            Submit deletion request
          </Button>
        </Card>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
