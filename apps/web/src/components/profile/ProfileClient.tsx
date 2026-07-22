"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { UserProfile } from "@rtas/shared";
import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
  type PaidPlanType,
} from "@rtas/shared";
import { applyCreditExpiry, saveProfile } from "@/lib/store";
import { Alert, Button, ButtonLink, Card, EmptyState } from "@rtas/ui";
import { shouldConfirmEarlyResubscribe } from "@/lib/monetization";
import { startCheckout } from "@/lib/checkout-client";
import { useStudioProfile } from "@/context/StudioProfileContext";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { ProfileAssetGallery } from "@/components/gallery/ProfileAssetGallery";
import { DashboardWelcome } from "@/components/profile/DashboardWelcome";
import {
  EmptyActivityIcon,
  EmptyProjectsIcon,
} from "@/components/profile/dashboard-empty-icons";
import {
  loadRecentProjects,
  type RecentProject,
} from "@/lib/studio-workflow-store";
import {
  draftHasRestorableContent,
  loadStudioDraft,
  type StudioDraftSnapshot,
} from "@/lib/studio-form-backup";

const EarlyResubscribeModal = dynamic(
  () =>
    import("@/components/EarlyResubscribeModal").then(
      (mod) => mod.EarlyResubscribeModal
    ),
  { ssr: false }
);

type Props = {
  initialProfile: UserProfile;
};

function firstName(name: string): string {
  const part = name.trim().split(/\s+/)[0];
  return part || "there";
}

function formatRelative(iso: string): string {
  const t = new Date(iso).getTime();
  if (!Number.isFinite(t)) return "";
  const diff = Date.now() - t;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function jobStatusLabel(status: string): string {
  const s = status.toLowerCase();
  if (s.includes("fail")) return "Failed";
  if (s.includes("complete") || s === "ready" || s === "succeeded") return "Ready";
  if (s.includes("queue") || s.includes("wait")) return "Queued";
  if (s.includes("render") || s.includes("generat") || s.includes("process") || s === "running") {
    return "Rendering";
  }
  return status || "Update";
}

export function ProfileClient({ initialProfile }: Props) {
  const {
    profile: contextProfile,
    syncFromServer,
    setProfile: setContextProfile,
    studioMetrics,
    generationLimitReached,
    generationLimitMessage,
  } = useStudioProfile();
  const [profile, setProfile] = useState(initialProfile);
  const [showEarlyResubscribe, setShowEarlyResubscribe] = useState(false);
  const [pendingPlan, setPendingPlan] = useState<PaidPlanType>("standard");
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [busyPlan, setBusyPlan] = useState<PaidPlanType | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [draft, setDraft] = useState<StudioDraftSnapshot | null>(null);
  const [showPlans, setShowPlans] = useState(false);

  useEffect(() => {
    const current = applyCreditExpiry(initialProfile);
    saveProfile(current);
    setProfile(current);
    setContextProfile(current);
    setSyncError(null);
    void syncFromServer(current.id)
      .then((synced) => {
        if (synced) setProfile(synced);
      })
      .catch(() => {
        setSyncError("Couldn't refresh account status. Showing your last saved details.");
      });
  }, [initialProfile.id, setContextProfile, syncFromServer]);

  useEffect(() => {
    if (contextProfile && contextProfile.id === initialProfile.id) {
      setProfile(contextProfile);
    }
  }, [contextProfile, initialProfile.id]);

  useEffect(() => {
    setRecentProjects(loadRecentProjects());
    const d = loadStudioDraft();
    setDraft(d && draftHasRestorableContent(d) ? d : null);
    setHydrated(true);
  }, []);

  const runCheckout = async (
    plan: PaidPlanType,
    options?: { rolloverRemaining?: boolean }
  ) => {
    if (checkoutBusy) return;
    setCheckoutBusy(true);
    setBusyPlan(plan);
    setStatus(null);
    try {
      const result = await startCheckout(profile, plan, options);
      if (result.profile) {
        saveProfile(result.profile);
        setProfile(result.profile);
      }
      if (result.message) setStatus(result.message);
      else if (result.openedUrl) setStatus("Checkout opened in a new tab.");
    } finally {
      setCheckoutBusy(false);
      setBusyPlan(null);
    }
  };

  const onMonthlyClick = (plan: "standard" | "premium") => {
    if (shouldConfirmEarlyResubscribe(profile) && profile.tier === plan) {
      setPendingPlan(plan);
      setShowEarlyResubscribe(true);
      return;
    }
    void runCheckout(plan);
  };

  const tierLabel =
    profile.tier === "premium"
      ? "Premium 4K"
      : profile.tier === "standard"
        ? "Standard"
        : profile.tier === "tester"
          ? "Tester"
          : "Free";

  const credits = profile.credits;
  const queueActive =
    studioMetrics?.concurrentTracks ?? studioMetrics?.renderingQueues ?? 0;
  const queueMax = studioMetrics?.maxConcurrentGenerations ?? 3;
  const recentJobs = studioMetrics?.recentJobs ?? [];
  const activeJobs = recentJobs.filter((j) => {
    const s = j.status.toLowerCase();
    return !(
      s.includes("complete") ||
      s.includes("fail") ||
      s === "ready" ||
      s === "succeeded"
    );
  });

  const continueProject = useMemo(() => {
    if (draft) {
      const title =
        draft.text.videoTitle?.trim() ||
        draft.text.mainPrompt?.trim()?.slice(0, 48) ||
        draft.text.directionPrompt?.trim()?.slice(0, 48) ||
        "Untitled draft";
      return {
        kind: "draft" as const,
        title,
        meta: `Autosaved ${formatRelative(draft.savedAt)}`,
        href: "/studio",
      };
    }
    const latest = recentProjects[0];
    if (latest) {
      return {
        kind: "recent" as const,
        title: latest.title || "Recent project",
        meta: `${latest.status === "ready" ? "Ready" : latest.status} · ${formatRelative(latest.createdAt)}`,
        href: "/studio",
      };
    }
    return null;
  }, [draft, recentProjects]);

  const isFirstTime =
    hydrated &&
    !draft &&
    recentProjects.length === 0 &&
    recentJobs.length === 0 &&
    !profile.freeTrialUsed &&
    !profile.hasUsedFreeTrial &&
    !profile.subscriptionActive;

  const notifications = useMemo(() => {
    const items: Array<{ id: string; tone: "info" | "warn" | "ok"; text: string }> = [];
    if (activeJobs.length > 0) {
      items.push({
        id: "active",
        tone: "info",
        text: `${activeJobs.length} generation${activeJobs.length === 1 ? "" : "s"} currently rendering`,
      });
    }
    if (generationLimitReached) {
      items.push({
        id: "limit",
        tone: "warn",
        text: generationLimitMessage ?? "Render queue is full. Wait for a free slot, then try again.",
      });
    }
    if (credits <= 0 && !profile.subscriptionActive) {
      items.push({
        id: "credits",
        tone: "warn",
        text: `No credits yet — start with Tester $${TESTER_PRICE_USD} (${TESTER_CREDITS}s / ${TESTER_DURATION_DAYS} days).`,
      });
    } else if (credits <= 0) {
      items.push({
        id: "credits",
        tone: "warn",
        text: "You are out of credits. Upgrade your plan to continue creating.",
      });
    } else if (
      profile.creditsExpireAt &&
      new Date(profile.creditsExpireAt).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000
    ) {
      items.push({
        id: "expiry",
        tone: "warn",
        text: `Credits expire on ${new Date(profile.creditsExpireAt).toLocaleDateString()}`,
      });
    }
    if (draft) {
      items.push({
        id: "draft",
        tone: "ok",
        text: "Autosaved Studio draft is ready to continue",
      });
    }
    return items.slice(0, 4);
  }, [
    activeJobs.length,
    generationLimitReached,
    generationLimitMessage,
    credits,
    profile.subscriptionActive,
    profile.creditsExpireAt,
    draft,
  ]);

  const activityItems = useMemo(() => {
    const fromJobs = recentJobs.slice(0, 6).map((j) => ({
      id: `job-${j.id}`,
      title: j.prompt?.trim()?.slice(0, 56) || "Studio render",
      meta: `${jobStatusLabel(j.status)} · ${formatRelative(j.createdAt)}`,
      status: jobStatusLabel(j.status),
    }));
    if (fromJobs.length > 0) return fromJobs;
    return recentProjects.slice(0, 6).map((p) => ({
      id: `proj-${p.id}`,
      title: p.title,
      meta: `${p.status} · ${formatRelative(p.createdAt)}`,
      status: p.status === "ready" ? "Ready" : p.status,
    }));
  }, [recentJobs, recentProjects]);

  const greeting = `Welcome${profile.name ? `, ${firstName(profile.name)}` : ""}`;

  return (
    <MarketingLayout>
      <div className="rtas-profile-wrap rtas-profile-wrap--with-gallery profile-page profile-page--dashboard video-content-panel">
        <EarlyResubscribeModal
          open={showEarlyResubscribe}
          remainingCredits={profile.credits}
          creditsExpireAt={profile.creditsExpireAt}
          onConfirm={() => void runCheckout(pendingPlan, { rolloverRemaining: true })}
          onCancel={() => setShowEarlyResubscribe(false)}
        />

        <a href="#dashboard-main" className="dashboard-skip">
          Skip to dashboard
        </a>

        <nav className="dashboard-nav" aria-label="Dashboard">
          <Link href="/studio" className="dashboard-nav__back">
            ← Studio
          </Link>
          <span className="dashboard-nav__crumb" aria-current="page">
            Dashboard
          </span>
        </nav>

        <DashboardWelcome
          firstName={profile.name ? firstName(profile.name) : undefined}
        />

        <header className="dashboard-hero" id="dashboard-main">
          <div className="dashboard-hero__copy">
            <p className="dashboard-hero__eyebrow">{tierLabel} plan</p>
            <h1 className="dashboard-hero__title">{greeting}</h1>
            <p className="dashboard-hero__sub">
              {isFirstTime
                ? "Create your first cinematic video in Studio. Finished renders appear in Your library below."
                : "Resume projects, monitor credits, and track recent generations from one place."}
            </p>
          </div>
          <div className="dashboard-hero__actions">
            <ButtonLink
              href="/studio"
              variant="lavender"
              className="dashboard-cta-primary"
            >
              {isFirstTime ? "Create your first video" : "Open Studio"}
            </ButtonLink>
            {isFirstTime ? (
              <ButtonLink href="/how-to-use" variant="ghost">
                Quick start guide
              </ButtonLink>
            ) : null}
            {continueProject ? (
              <Link href={continueProject.href} className="dashboard-continue">
                <span className="dashboard-continue__label">Continue</span>
                <span className="dashboard-continue__title">{continueProject.title}</span>
                <span className="dashboard-continue__meta">{continueProject.meta}</span>
              </Link>
            ) : null}
          </div>
        </header>

        {syncError ? (
          <Alert
            variant="warning"
            title="Sync issue"
            message={syncError}
            onDismiss={() => setSyncError(null)}
            className="dashboard-alert"
          />
        ) : null}

        {status ? (
          <Alert
            variant="info"
            message={status}
            onDismiss={() => setStatus(null)}
            className="dashboard-alert profile-status-alert"
          />
        ) : null}

        <section className="dashboard-status" aria-label="Usage and credits">
          <Card
            as="article"
            variant="glass"
            className="dashboard-card dashboard-card--credits"
            aria-labelledby="dash-credits"
          >
            <h2 id="dash-credits" className="dashboard-card__label">
              Usage &amp; credits
            </h2>
            <p className="dashboard-card__value" aria-live="polite">
              {credits}
              <span className="dashboard-card__unit">seconds</span>
            </p>
            <p className="dashboard-card__hint">1 credit = 1 second of finished video</p>
            {profile.creditsExpireAt ? (
              <p className="dashboard-card__meta">
                Expires {new Date(profile.creditsExpireAt).toLocaleDateString()}
              </p>
            ) : (
              <p className="dashboard-card__meta">
                {profile.subscriptionActive
                  ? "Subscription active — credits renew with your plan"
                  : "No active subscription"}
              </p>
            )}
          </Card>

          <Card as="article" variant="glass" className="dashboard-card" aria-labelledby="dash-gen">
            <h2 id="dash-gen" className="dashboard-card__label">
              Render queue
            </h2>
            <p className="dashboard-card__value dashboard-card__value--sm">
              {activeJobs.length > 0
                ? `${activeJobs.length} active`
                : queueActive > 0
                  ? `${queueActive} in queue`
                  : "Idle"}
            </p>
            <p className="dashboard-card__hint">
              Slots {queueActive}/{queueMax}
              {generationLimitReached ? " · full" : " available"}
            </p>
            <div className="dashboard-queue" aria-hidden>
              {Array.from({ length: queueMax }).map((_, i) => (
                <span
                  key={i}
                  className={
                    i < Math.min(queueActive, queueMax)
                      ? "dashboard-queue__slot dashboard-queue__slot--busy"
                      : "dashboard-queue__slot"
                  }
                />
              ))}
            </div>
          </Card>

          <Card as="article" variant="glass" className="dashboard-card" aria-labelledby="dash-notes">
            <h2 id="dash-notes" className="dashboard-card__label">
              Alerts
            </h2>
            {notifications.length === 0 ? (
              <p className="dashboard-card__empty">
                {isFirstTime
                  ? `Plans start at Tester $${TESTER_PRICE_USD} — ${TESTER_CREDITS} seconds for ${TESTER_DURATION_DAYS} days.`
                  : "You are all caught up. No action needed."}
              </p>
            ) : (
              <ul className="dashboard-notes">
                {notifications.map((n) => (
                  <li key={n.id} className={`dashboard-notes__item dashboard-notes__item--${n.tone}`}>
                    {n.text}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </section>

        <section className="dashboard-section" aria-labelledby="dash-actions">
          <div className="dashboard-section__head">
            <h2 id="dash-actions">Quick actions</h2>
            <p className="dashboard-section__sub">Jump into Studio, library, or billing</p>
          </div>
          <div className="dashboard-actions" role="list">
            <Link href="/studio" className="dashboard-action" role="listitem">
              <span className="dashboard-action__title">New video</span>
              <span className="dashboard-action__desc">Open Studio and start a generation</span>
            </Link>
            <a href="#your-renders" className="dashboard-action" role="listitem">
              <span className="dashboard-action__title">Your library</span>
              <span className="dashboard-action__desc">Browse finished and in-progress renders</span>
            </a>
            <button
              type="button"
              className="dashboard-action"
              role="listitem"
              onClick={() => {
                setShowPlans(true);
                requestAnimationFrame(() => {
                  document.getElementById("dashboard-billing")?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                });
              }}
            >
              <span className="dashboard-action__title">Billing &amp; plans</span>
              <span className="dashboard-action__desc">Upgrade credits · Tester, Standard, Premium</span>
            </button>
            <Link href="/pricing#plans" className="dashboard-action" role="listitem">
              <span className="dashboard-action__title">Compare pricing</span>
              <span className="dashboard-action__desc">See plans, credits, and commercial rights</span>
            </Link>
            <Link href="/how-to-use" className="dashboard-action" role="listitem">
              <span className="dashboard-action__title">Product guide</span>
              <span className="dashboard-action__desc">Learn Studio in under a minute</span>
            </Link>
            <Link href="/help" className="dashboard-action" role="listitem">
              <span className="dashboard-action__title">Help Center</span>
              <span className="dashboard-action__desc">FAQ, billing help, and troubleshooting</span>
            </Link>
          </div>
        </section>

        <div className="dashboard-split">
          <section className="dashboard-section" aria-labelledby="dash-recent">
            <div className="dashboard-section__head">
              <h2 id="dash-recent">Projects</h2>
              <Link href="/studio" className="dashboard-section__link">
                Open Studio
              </Link>
            </div>
            {!hydrated ? (
              <div className="dashboard-skeleton" aria-busy="true" aria-label="Loading recent projects">
                <div className="dashboard-skeleton__row" />
                <div className="dashboard-skeleton__row" />
                <div className="dashboard-skeleton__row" />
              </div>
            ) : recentProjects.length === 0 && !draft ? (
              <EmptyState
                className="dashboard-empty"
                icon={<EmptyProjectsIcon />}
                title="No projects yet"
                description="Choose a category in Studio to begin. Drafts autosave as you work, and finished videos appear here and in Your library."
                actionLabel="Start creating"
                actionHref="/studio"
                secondaryActionLabel="View pricing"
                secondaryActionHref="/pricing"
              />
            ) : (
              <ul className="dashboard-list">
                {draft ? (
                  <li>
                    <Link href="/studio" className="dashboard-list__item dashboard-list__item--draft">
                      <span className="dashboard-list__title">
                        {continueProject?.title ?? "Autosaved draft"}
                      </span>
                      <span className="dashboard-list__meta">Draft · Continue in Studio</span>
                    </Link>
                  </li>
                ) : null}
                {recentProjects.slice(0, 5).map((p) => (
                  <li key={p.id}>
                    <Link href="/studio" className="dashboard-list__item">
                      <span className="dashboard-list__title">{p.title}</span>
                      <span className="dashboard-list__meta">
                        {p.category ? `${p.category} · ` : ""}
                        {formatRelative(p.createdAt)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="dashboard-section" aria-labelledby="dash-activity">
            <div className="dashboard-section__head">
              <h2 id="dash-activity">Recent generations</h2>
              <a href="#your-renders" className="dashboard-section__link">
                View library
              </a>
            </div>
            {!hydrated ? (
              <div className="dashboard-skeleton" aria-busy="true" aria-label="Loading activity">
                <div className="dashboard-skeleton__row" />
                <div className="dashboard-skeleton__row" />
                <div className="dashboard-skeleton__row" />
              </div>
            ) : activityItems.length === 0 ? (
              <EmptyState
                className="dashboard-empty"
                icon={<EmptyActivityIcon />}
                title="No generations yet"
                description="Queue updates, render history, and project activity appear here after your first Studio session."
                actionLabel="Open Studio"
                actionHref="/studio"
                secondaryActionLabel="Help Center"
                secondaryActionHref="/help"
              />
            ) : (
              <ol className="dashboard-timeline">
                {activityItems.map((item) => (
                  <li key={item.id} className="dashboard-timeline__item">
                    <span className="dashboard-timeline__dot" aria-hidden />
                    <div>
                      <p className="dashboard-timeline__title">{item.title}</p>
                      <p className="dashboard-timeline__meta">{item.meta}</p>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>

        <section
          className="dashboard-section dashboard-account"
          id="dashboard-billing"
          aria-labelledby="dash-account"
        >
          <div className="dashboard-section__head">
            <h2 id="dash-account">Billing &amp; subscription</h2>
            <button
              type="button"
              className="dashboard-section__link"
              aria-expanded={showPlans}
              onClick={() => setShowPlans((v) => !v)}
            >
              {showPlans ? "Hide plans" : "Manage subscription"}
            </button>
          </div>
          <p className="dashboard-section__lead">
            Review your account details and upgrade options. Checkout opens in a
            secure new tab. 1 credit = 1 second of finished video.
          </p>
          <div className="dashboard-account__grid">
            <Card variant="glass" className="dashboard-card dashboard-card--static">
              <p>
                <strong>Name</strong>
                <span>{profile.name || "—"}</span>
              </p>
              <p>
                <strong>Email</strong>
                <span>{profile.email || "—"}</span>
              </p>
              {profile.paymentProvider ? (
                <p>
                  <strong>Billing provider</strong>
                  <span>{profile.paymentProvider}</span>
                </p>
              ) : (
                <p>
                  <strong>Billing provider</strong>
                  <span>Not connected</span>
                </p>
              )}
            </Card>
            <Card variant="glass" className="dashboard-card dashboard-card--static">
              <p>
                <strong>Credits</strong>
                <span>
                  {credits} second{credits === 1 ? "" : "s"}
                </span>
              </p>
              <p>
                <strong>Subscription</strong>
                <span>{profile.subscriptionActive ? "Active" : "None"}</span>
              </p>
              <p>
                <strong>Current plan</strong>
                <span>{tierLabel}</span>
              </p>
            </Card>
          </div>

          {!showPlans ? (
            <div className="dashboard-billing-cta">
              <Button
                variant="lavender"
                onClick={() => setShowPlans(true)}
              >
                {profile.subscriptionActive ? "Change plan" : "View upgrade options"}
              </Button>
              <ButtonLink href="/pricing#plans" variant="ghost">
                Full pricing page
              </ButtonLink>
              <ButtonLink href="/help/billing" variant="ghost">
                Billing help
              </ButtonLink>
            </div>
          ) : null}

          {showPlans ? (
            <div className="profile-checkout-row dashboard-plans" id="dashboard-plans">
              <p className="dashboard-plans__hint">
                Select a plan to add credits. Checkout opens in a new tab — you can return here when
                finished.
              </p>
              <Button
                variant="secondary"
                className="profile-sub-btn"
                disabled={checkoutBusy}
                loading={busyPlan === "tester"}
                loadingLabel="Opening checkout…"
                onClick={() => void runCheckout("tester")}
              >
                Tester — ${TESTER_PRICE_USD} · {TESTER_CREDITS}s · {TESTER_DURATION_DAYS} days
              </Button>
              <Button
                variant="primary"
                className="profile-sub-btn"
                disabled={checkoutBusy}
                loading={busyPlan === "standard"}
                loadingLabel="Opening checkout…"
                onClick={() => onMonthlyClick("standard")}
              >
                Standard — ${STANDARD_PRICE_USD}/mo · {STANDARD_CREDITS}s
              </Button>
              <Button
                variant="primary"
                className="profile-sub-btn"
                disabled={checkoutBusy}
                loading={busyPlan === "premium"}
                loadingLabel="Opening checkout…"
                onClick={() => onMonthlyClick("premium")}
              >
                Premium 4K — ${PREMIUM_PRICE_USD}/mo · {PREMIUM_CREDITS}s
              </Button>
            </div>
          ) : null}
        </section>

        <div id="your-renders">
          <ProfileAssetGallery userId={profile.id} />
        </div>

        <footer className="profile-legal">
          <Link href="/terms">Terms of Service</Link>
          <Link href="/privacy">Privacy Policy</Link>
          <Link href="/refund">Refund Policy</Link>
          <Link href="/cookies">Cookies</Link>
          <Link href="/pricing#plans">Pricing</Link>
        </footer>
      </div>
    </MarketingLayout>
  );
}
