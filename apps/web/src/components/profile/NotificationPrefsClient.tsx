"use client";

import { useCallback, useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Alert, Button, Card } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import type {
  InAppAnnouncement,
  NotificationChannelPrefs,
} from "@/lib/marketing/notifications";

const LABELS: { key: keyof NotificationChannelPrefs; label: string; locked?: boolean }[] = [
  { key: "emailTransactional", label: "Transactional email (auth, security)", locked: true },
  { key: "emailBilling", label: "Billing email" },
  { key: "emailProduct", label: "Product email (video ready, tips)" },
  { key: "emailMarketing", label: "Marketing / newsletter email" },
  { key: "inAppAnnouncements", label: "In-app announcements" },
  { key: "inAppSecurity", label: "In-app security notices" },
  { key: "inAppBilling", label: "In-app billing notices" },
  { key: "inAppMaintenance", label: "In-app maintenance notices" },
];

export function NotificationPrefsClient() {
  const { status } = useSession();
  const [prefs, setPrefs] = useState<NotificationChannelPrefs | null>(null);
  const [announcements, setAnnouncements] = useState<InAppAnnouncement[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/user/notifications");
      const json = (await res.json()) as {
        ok?: boolean;
        prefs?: NotificationChannelPrefs;
        announcements?: InAppAnnouncement[];
        error?: string;
      };
      if (!res.ok || !json.ok || !json.prefs) {
        throw new Error(json.error ?? "Could not load preferences.");
      }
      setPrefs(json.prefs);
      setAnnouncements(json.announcements ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (status === "authenticated") void load();
  }, [status, load]);

  async function save() {
    if (!prefs) return;
    setBusy(true);
    setSaved(false);
    setError(null);
    try {
      const res = await fetch("/api/user/notifications", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      });
      const json = (await res.json()) as {
        ok?: boolean;
        prefs?: NotificationChannelPrefs;
        error?: string;
      };
      if (!res.ok || !json.ok || !json.prefs) {
        throw new Error(json.error ?? "Save failed.");
      }
      setPrefs(json.prefs);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  if (status === "unauthenticated") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection className="pt-8">
            <h1 className="font-display text-4xl text-ds-text">Notifications</h1>
            <p className="mt-3 text-ds-text-muted">Sign in to manage email and in-app preferences.</p>
            <Link
              href="/auth/signin?callbackUrl=/profile/notifications"
              className="mt-6 inline-block text-ds-accent"
            >
              Sign in →
            </Link>
          </InnerPageSection>
        </InnerPageContainer>
      </MarketingLayout>
    );
  }

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="pt-8">
          <h1 className="font-display text-4xl text-ds-text">Notification Center</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Control email and in-app channels for announcements, maintenance, security, and
            billing. Transactional auth email stays on.
          </p>
        </InnerPageSection>

        {error && <Alert variant="error" message={error} />}
        {saved && <Alert variant="info" message="Preferences saved." />}

        <Card className="space-y-3 p-5">
          {prefs &&
            LABELS.map((row) => (
              <label
                key={row.key}
                className="flex items-center justify-between gap-4 border-b border-white/5 py-2 text-sm"
              >
                <span className="text-zinc-200">
                  {row.label}
                  {row.locked ? " (required)" : ""}
                </span>
                <input
                  type="checkbox"
                  checked={prefs[row.key]}
                  disabled={row.locked || busy}
                  onChange={(e) =>
                    setPrefs({ ...prefs, [row.key]: e.target.checked })
                  }
                />
              </label>
            ))}
          <Button type="button" variant="primary" disabled={busy || !prefs} onClick={() => void save()}>
            Save preferences
          </Button>
        </Card>

        <InnerPageSection>
          <h2 className="text-xl text-ds-text">Active announcements</h2>
          <ul className="mt-3 space-y-3">
            {announcements.map((a) => (
              <li key={a.id} className="rounded-lg border border-white/10 p-4">
                <p className="text-xs uppercase text-ds-text-muted">{a.kind}</p>
                <p className="mt-1 font-medium text-zinc-100">{a.title}</p>
                <p className="mt-1 text-sm text-ds-text-muted">{a.body}</p>
                {a.href ? (
                  <Link href={a.href} className="mt-2 inline-block text-sm text-ds-accent">
                    Open →
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
