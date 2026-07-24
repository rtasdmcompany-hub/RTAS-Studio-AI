"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import type { UserProfile } from "@rtas/shared";
import type { StudioMetricsState } from "@/context/StudioProfileContext";
import type { RecentProject } from "@/lib/studio-workflow-store";

type Props = {
  profile: UserProfile;
  recentProjects: RecentProject[];
  recentJobs: StudioMetricsState["recentJobs"];
  hydrated: boolean;
};

type ChecklistItem = {
  id: string;
  label: string;
  done: boolean;
  hint: string;
  href?: string;
};

/**
 * Founder/user-facing success checklist for the signed-in account only.
 * Never fabricates metrics for other users.
 */
export function CustomerSuccessChecklist({
  profile,
  recentProjects,
  recentJobs,
  hydrated,
}: Props) {
  const { data: session, status } = useSession();

  const emailVerified =
    session?.user?.emailVerified === true ||
    // Middleware already blocks unverified users from /profile; treat unknown as verified once here.
    (status === "authenticated" && session?.user?.emailVerified !== false);

  const firstLogin = status === "authenticated";

  const hasProject =
    recentProjects.length > 0 ||
    recentJobs.length > 0 ||
    Boolean(profile.freeTrialUsed || profile.hasUsedFreeTrial);

  const hasVideo = recentJobs.some((j) => {
    const s = j.status.toLowerCase();
    return (
      Boolean(j.generatedVideoUrl) ||
      s.includes("complete") ||
      s === "ready" ||
      s === "succeeded"
    );
  }) ||
    recentProjects.some((p) => p.status === "ready") ||
    Boolean(profile.freeTrialUsed || profile.hasUsedFreeTrial);

  const creditsUsed =
    recentJobs.some((j) => (j.creditsCharged ?? 0) > 0) ||
    Boolean(profile.freeTrialUsed || profile.hasUsedFreeTrial);

  const subscriptionLabel = profile.subscriptionActive
    ? `${profile.tier === "premium" ? "Premium 4K" : profile.tier === "standard" ? "Standard" : profile.tier === "tester" ? "Tester" : "Active"} · active`
    : profile.tier === "free"
      ? "Free · no paid plan yet"
      : `${profile.tier} · inactive`;

  const items: ChecklistItem[] = [
    {
      id: "account",
      label: "Account created",
      done: Boolean(profile.id && profile.createdAt),
      hint: profile.createdAt
        ? `Since ${new Date(profile.createdAt).toLocaleDateString()}`
        : "Your RTAS account exists",
    },
    {
      id: "verified",
      label: "Email verified",
      done: emailVerified,
      hint: emailVerified
        ? profile.email || "Verified for Studio access"
        : "Confirm the link in your inbox",
      href: emailVerified ? undefined : "/auth/check-email",
    },
    {
      id: "login",
      label: "First login",
      done: firstLogin,
      hint: firstLogin ? "You are signed in on this device" : "Sign in to continue",
      href: firstLogin ? undefined : "/auth/login",
    },
    {
      id: "project",
      label: "First project",
      done: hydrated && hasProject,
      hint: hydrated
        ? hasProject
          ? "Draft, project, or render recorded"
          : "Open Studio and save a compose"
        : "Loading…",
      href: hasProject ? undefined : "/studio",
    },
    {
      id: "video",
      label: "First video",
      done: hydrated && hasVideo,
      hint: hydrated
        ? hasVideo
          ? "At least one render completed or trial used"
          : "Generate your first clip in Studio"
        : "Loading…",
      href: hasVideo ? undefined : "/studio",
    },
    {
      id: "credits",
      label: "Credits used",
      done: creditsUsed,
      hint: creditsUsed
        ? "Generation credits were charged on your account"
        : `Balance: ${profile.credits}s — render to spend credits`,
      href: creditsUsed ? undefined : "/studio",
    },
    {
      id: "subscription",
      label: "Subscription status",
      done: profile.subscriptionActive,
      hint: subscriptionLabel,
      href: profile.subscriptionActive ? undefined : "/pricing#plans",
    },
  ];

  const doneCount = items.filter((i) => i.done).length;

  return (
    <section
      className="dashboard-section dashboard-success"
      aria-labelledby="dash-success"
    >
      <div className="dashboard-section__head">
        <h2 id="dash-success">Getting started checklist</h2>
        <p className="dashboard-section__sub">
          Your account only — {doneCount}/{items.length} complete. No team-wide or invented
          metrics.
        </p>
      </div>
      <ul className="dashboard-success__list">
        {items.map((item) => (
          <li
            key={item.id}
            className={
              item.done
                ? "dashboard-success__item dashboard-success__item--done"
                : "dashboard-success__item"
            }
          >
            <span className="dashboard-success__mark" aria-hidden>
              {item.done ? "✓" : "○"}
            </span>
            <div className="dashboard-success__copy">
              <span className="dashboard-success__label">{item.label}</span>
              <span className="dashboard-success__hint">{item.hint}</span>
            </div>
            {!item.done && item.href ? (
              <Link href={item.href} className="dashboard-success__cta">
                Continue →
              </Link>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
