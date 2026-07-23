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
import type { ReferralSummary } from "@/lib/marketing/referral";

export function ReferralClient() {
  const { status } = useSession();
  const [data, setData] = useState<ReferralSummary | null>(null);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/user/referral");
      const json = (await res.json()) as {
        ok?: boolean;
        referral?: ReferralSummary;
        error?: string;
      };
      if (!res.ok || !json.ok || !json.referral) {
        throw new Error(json.error ?? "Could not load referral.");
      }
      setData(json.referral);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (status === "authenticated") void load();
  }, [status, load]);

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      const res = await fetch("/api/user/referral", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const json = (await res.json()) as {
        ok?: boolean;
        referral?: ReferralSummary;
        error?: string;
        note?: string;
      };
      if (!res.ok || !json.ok) {
        throw new Error(json.error ?? "Invite failed.");
      }
      setData(json.referral ?? null);
      setNote(json.note ?? "Invite recorded.");
      setEmail("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invite failed.");
    } finally {
      setBusy(false);
    }
  }

  if (status === "unauthenticated") {
    return (
      <MarketingLayout>
        <InnerPageContainer>
          <InnerPageSection className="pt-8">
            <h1 className="font-display text-4xl text-ds-text">Referral program</h1>
            <p className="mt-3 text-ds-text-muted">
              Sign in to get your invite link and code. Rewards are labeled Proposed until live.
            </p>
            <Link
              href="/auth/signin?callbackUrl=/referral"
              className="mt-6 inline-block text-ds-accent underline-offset-4 hover:underline"
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
          <p className="text-xs uppercase tracking-wide text-amber-200/90">
            Proposed — rewards not auto-granted
          </p>
          <h1 className="mt-2 font-display text-4xl text-ds-text">Invite & earn</h1>
          <p className="mt-3 max-w-2xl text-ds-text-muted">
            Share your link or code. Tracking and history are stored when the database is
            available. Credit rewards stay Proposed until ops enables grants.
          </p>
        </InnerPageSection>

        {error && <Alert variant="error" message={error} />}
        {note && <Alert variant="info" message={note} />}

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="p-5">
            <h2 className="text-lg text-zinc-100">Your code</h2>
            <p className="mt-3 font-mono text-2xl text-ds-accent">
              {data?.code ?? (busy ? "…" : "—")}
            </p>
            <p className="mt-3 break-all text-sm text-ds-text-muted">
              {data?.link ?? "Link appears after load."}
            </p>
            {data?.link ? (
              <Button
                className="mt-4"
                variant="secondary"
                type="button"
                onClick={() => void navigator.clipboard.writeText(data.link!)}
              >
                Copy link
              </Button>
            ) : null}
          </Card>

          <Card className="p-5">
            <h2 className="text-lg text-zinc-100">Proposed rewards</h2>
            <ul className="mt-3 space-y-2 text-sm text-ds-text-muted">
              <li>
                Referrer: {data?.proposedRewards.referrerCredits ?? 30} credits (Proposed)
              </li>
              <li>
                Friend: {data?.proposedRewards.referredCredits ?? 15} credits (Proposed)
              </li>
              <li>{data?.proposedRewards.note}</li>
            </ul>
            <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-ds-text-muted">Invites</p>
                <p className="text-xl text-zinc-100">{data?.invitesSent ?? 0}</p>
              </div>
              <div>
                <p className="text-ds-text-muted">Signed up</p>
                <p className="text-xl text-zinc-100">{data?.signedUp ?? 0}</p>
              </div>
              <div>
                <p className="text-ds-text-muted">Converted</p>
                <p className="text-xl text-zinc-100">{data?.converted ?? 0}</p>
              </div>
              <div>
                <p className="text-ds-text-muted">Rewards granted</p>
                <p className="text-xl text-zinc-100">{data?.rewardsGranted ?? 0}</p>
              </div>
            </div>
          </Card>
        </div>

        <InnerPageSection className="inner-page-section--panel">
          <h2 className="text-xl text-ds-text">Send invite</h2>
          <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={invite}>
            <input
              type="email"
              required
              placeholder="colleague@company.com"
              className="flex-1 rounded-md border border-white/10 bg-black/20 px-3 py-2 text-ds-text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" variant="primary" disabled={busy}>
              Record invite
            </Button>
          </form>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-ds-text">History</h2>
          {(data?.history?.length ?? 0) === 0 ? (
            <p className="mt-2 text-sm text-ds-text-muted">No invites yet (0).</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {data!.history.map((h) => (
                <li
                  key={h.id}
                  className="flex flex-wrap justify-between gap-2 border-b border-white/5 py-2"
                >
                  <span className="text-ds-text-muted">{h.referredEmail}</span>
                  <span className="text-zinc-300">
                    {h.status} · {new Date(h.invitedAt).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
