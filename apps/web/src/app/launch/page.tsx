import type { Metadata } from "next";
import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";
import {
  checklistProgress,
  LAUNCH_CHECKLIST,
  LAUNCH_MILESTONES,
  publicChecklist,
} from "@/lib/launch/checklist";
import { computeOverallReadiness, computeReadinessScores } from "@/lib/launch/readiness";

export const metadata: Metadata = buildPageMetadata({
  title: "Launch Center",
  description: `Global go-to-market launch center for ${PRODUCT_NAME} — timeline, checklist, milestones, and internal task owners. No fabricated campaign results.`,
  path: "/launch",
  openGraphTitle: `Launch Center · ${PRODUCT_NAME}`,
});

const STATUS_LABEL: Record<string, string> = {
  done: "Done",
  in_progress: "In progress",
  planned: "Planned",
  blocked: "Blocked",
  not_started: "Not started",
};

export default function LaunchCenterPage() {
  const publicItems = publicChecklist();
  const progress = checklistProgress(LAUNCH_CHECKLIST);
  const readiness = computeReadinessScores();
  const overall = computeOverallReadiness(readiness);
  const internalItems = LAUNCH_CHECKLIST.filter((i) => i.internal);

  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Go-to-market</p>
          <h1 className="text-zinc-100">Launch Center</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            International launch timeline, checklist, and milestones for {PRODUCT_NAME}.
            Statuses reflect real work — never invented traffic, press, or revenue.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/launch/campaigns" variant="lavender">
              Campaign plans
            </ButtonLink>
            <ButtonLink href="/launch/assets" variant="ghost">
              Asset library
            </ButtonLink>
            <ButtonLink href="/roadmap" variant="ghost">
              Public roadmap
            </ButtonLink>
            <ButtonLink href="/admin/launch" variant="ghost">
              Executive dashboard
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Launch status">
          <InnerPageSection className="inner-page-section--panel">
            <p className="text-xs uppercase tracking-wide text-ds-text-muted">Checklist done</p>
            <p className="mt-1 text-3xl font-semibold text-zinc-100">{progress.pct}%</p>
            <p className="mt-1 text-xs text-ds-text-muted">
              {progress.done}/{progress.total} items · {progress.blocked} blocked
            </p>
          </InnerPageSection>
          <InnerPageSection className="inner-page-section--panel">
            <p className="text-xs uppercase tracking-wide text-ds-text-muted">Overall readiness</p>
            <p className="mt-1 text-3xl font-semibold text-zinc-100">{overall.score}</p>
            <p className="mt-1 text-xs text-ds-text-muted">{overall.label}</p>
          </InnerPageSection>
          <InnerPageSection className="inner-page-section--panel">
            <p className="text-xs uppercase tracking-wide text-ds-text-muted">In progress</p>
            <p className="mt-1 text-3xl font-semibold text-zinc-100">{progress.inProgress}</p>
            <p className="mt-1 text-xs text-ds-text-muted">Active checklist tracks</p>
          </InnerPageSection>
          <InnerPageSection className="inner-page-section--panel">
            <p className="text-xs uppercase tracking-wide text-ds-text-muted">Milestones</p>
            <p className="mt-1 text-3xl font-semibold text-zinc-100">{LAUNCH_MILESTONES.length}</p>
            <p className="mt-1 text-xs text-ds-text-muted">Tracked launch phases</p>
          </InnerPageSection>
        </section>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Milestones</h2>
          <ol className="mt-6 space-y-4">
            {LAUNCH_MILESTONES.map((m, idx) => (
              <li
                key={m.id}
                className="border-l border-white/15 pl-4"
              >
                <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                  {idx + 1}. {STATUS_LABEL[m.status] ?? m.status} · {m.targetLabel}
                </p>
                <h3 className="mt-1 text-lg text-zinc-100">{m.title}</h3>
                <p className="mt-1 text-sm text-ds-text-muted">{m.summary}</p>
              </li>
            ))}
          </ol>
        </InnerPageSection>

        <InnerPageSection>
          <h2 className="text-xl text-zinc-100">Launch checklist</h2>
          <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
            Public view of launch tasks. Internal-only blockers are summarized separately for
            founders/admins.
          </p>
          <ul className="mt-6 space-y-3">
            {publicItems.map((item) => (
              <li
                key={item.id}
                className="flex flex-col gap-1 border-b border-white/10 pb-3 sm:flex-row sm:items-start sm:justify-between"
              >
                <div>
                  <p className="text-zinc-100">{item.title}</p>
                  <p className="text-sm text-ds-text-muted">{item.description}</p>
                  {item.evidence ? (
                    <p className="mt-1 text-xs text-ds-text-muted">Evidence: {item.evidence}</p>
                  ) : null}
                </div>
                <div className="shrink-0 text-sm text-ds-text-muted sm:text-right">
                  <p>{STATUS_LABEL[item.status]}</p>
                  <p className="text-xs">Owner: {item.owner}</p>
                </div>
              </li>
            ))}
          </ul>
        </InnerPageSection>

        <InnerPageSection className="inner-page-section--panel">
          <h2 className="text-xl text-zinc-100">Internal tasks (founder / admin)</h2>
          <p className="mt-2 text-sm text-ds-text-muted">
            Sensitive launch blockers — visible here for operator accountability. Prefer the
            locked{" "}
            <Link href="/admin/launch" className="underline underline-offset-2">
              Executive Launch Dashboard
            </Link>{" "}
            for scored readiness.
          </p>
          <ul className="mt-4 space-y-3">
            {internalItems.map((item) => (
              <li key={item.id} className="text-sm">
                <span className="text-zinc-100">{item.title}</span>
                <span className="text-ds-text-muted">
                  {" "}
                  — {STATUS_LABEL[item.status]} · {item.owner}
                  {item.evidence ? ` · ${item.evidence}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </InnerPageSection>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">Related</h2>
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/admin/acquisition" variant="ghost">
              Acquisition dashboard
            </ButtonLink>
            <ButtonLink href="/feedback" variant="ghost">
              Feedback portal
            </ButtonLink>
            <ButtonLink href="/success" variant="ghost">
              Customer success
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
