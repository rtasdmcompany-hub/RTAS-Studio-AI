/**
 * Phase 13 Sprint 9 — Launch Center checklist & milestones.
 * Statuses reflect real product/launch state from Phases 10–12 and Phase 13 GTM work.
 * Never mark items done without evidence.
 */

import type { LaunchChecklistItem, LaunchMilestone } from "./types";

export const LAUNCH_MILESTONES: LaunchMilestone[] = [
  {
    id: "m1-product-freeze",
    title: "Product freeze (RC)",
    targetLabel: "Complete",
    status: "done",
    summary:
      "Studio, auth, credits, MoR scaffolding, SEO, Help Center shipped as v1.0.0 RC.",
  },
  {
    id: "m2-commercial-wiring",
    title: "Commercial wiring",
    targetLabel: "In progress",
    status: "in_progress",
    summary:
      "Paddle config present; live purchase→credits E2E and live Fal generation still unproven on production.",
  },
  {
    id: "m3-gtm-system",
    title: "GTM launch system",
    targetLabel: "Sprint 9",
    status: "done",
    summary:
      "Launch Center, campaigns, acquisition, assets, roadmap, feedback portal, executive readiness shipped.",
  },
  {
    id: "m4-paid-acquisition",
    title: "Paid acquisition start",
    targetLabel: "Planned",
    status: "planned",
    summary:
      "Google Ads / Meta Ads structures ready; no live spend or fabricated ROAS until ads accounts + creative approved.",
  },
  {
    id: "m5-press-ph",
    title: "Press & Product Hunt",
    targetLabel: "Planned",
    status: "planned",
    summary:
      "Press kit guide and PH campaign plan exist; no fabricated rankings or coverage claims.",
  },
];

export const LAUNCH_CHECKLIST: LaunchChecklistItem[] = [
  // Infra
  {
    id: "infra-vercel",
    title: "Production web deploy (Vercel)",
    description: "rtasstudio.com serves marketing + app surfaces.",
    category: "infra",
    status: "done",
    owner: "ops",
    milestoneId: "m1-product-freeze",
    evidence: "Live apex domain + /api/health",
  },
  {
    id: "infra-db",
    title: "Postgres / Prisma production",
    description: "Supabase pooler connected for serverless.",
    category: "infra",
    status: "done",
    owner: "engineering",
    milestoneId: "m1-product-freeze",
  },
  {
    id: "infra-fal",
    title: "Fal.ai wallet funded for live generation",
    description: "Live video generation requires provider balance.",
    category: "infra",
    status: "blocked",
    owner: "ops",
    milestoneId: "m2-commercial-wiring",
    evidence: "Known limitation — not cleared as live E2E",
    internal: true,
  },
  {
    id: "infra-observability",
    title: "Observability (Sentry / analytics sinks)",
    description: "Public health may report analytics/sentry false until wired.",
    category: "infra",
    status: "in_progress",
    owner: "engineering",
    evidence: "Analytics architecture documented; vendor sinks Ready for Integration",
  },
  // Security
  {
    id: "sec-webhooks",
    title: "Paddle webhook fail-closed signatures",
    description: "Unsigned webhooks rejected in production.",
    category: "security",
    status: "done",
    owner: "engineering",
    evidence: "Phase 12 probe: 401 Invalid signature",
  },
  {
    id: "sec-auth-gates",
    title: "Auth gates on Studio / generate / checkout",
    description: "Unauthenticated generate/checkout return 401.",
    category: "security",
    status: "done",
    owner: "engineering",
  },
  {
    id: "sec-admin",
    title: "Admin routes secret-protected",
    description: "RTAS_ADMIN_SECRET required for admin APIs and dashboards.",
    category: "security",
    status: "done",
    owner: "engineering",
  },
  {
    id: "sec-csp",
    title: "CSP enforcement (vs Report-Only)",
    description: "CSP remains Report-Only pending embed QA.",
    category: "security",
    status: "planned",
    owner: "engineering",
  },
  // Marketing
  {
    id: "mkt-positioning",
    title: "Brand positioning & ICP docs",
    description: "Phase 13 Sprint 1 messaging pack.",
    category: "marketing",
    status: "done",
    owner: "marketing",
    evidence: "marketing/*.md",
  },
  {
    id: "mkt-launch-center",
    title: "Launch Center + campaign plans",
    description: "Structures for organic + paid channels without fake metrics.",
    category: "marketing",
    status: "done",
    owner: "marketing",
    milestoneId: "m3-gtm-system",
    evidence: "/launch, /launch/campaigns",
  },
  {
    id: "mkt-assets",
    title: "Launch asset library populated",
    description: "Real logos linked; screenshots/press media labeled when missing.",
    category: "marketing",
    status: "in_progress",
    owner: "marketing",
    evidence: "/launch/assets — placeholders remain for PNG/screenshots/media kit ZIP",
  },
  {
    id: "mkt-ph",
    title: "Product Hunt launch day runbook",
    description: "Plan only — no fabricated PH rank.",
    category: "marketing",
    status: "planned",
    owner: "marketing",
    milestoneId: "m5-press-ph",
  },
  // Sales
  {
    id: "sales-pricing",
    title: "Public pricing ($5 / $89 / $249)",
    description: "Tester, Standard, Premium on /pricing.",
    category: "sales",
    status: "done",
    owner: "sales",
  },
  {
    id: "sales-enterprise",
    title: "Enterprise / demo lead capture",
    description: "Commercial lead forms + CRM persistence.",
    category: "sales",
    status: "done",
    owner: "sales",
    evidence: "/enterprise, /demo, EnterpriseLead",
  },
  {
    id: "sales-paddle-e2e",
    title: "Live Paddle purchase → credits E2E",
    description: "Must be proven before paid acquisition scale.",
    category: "sales",
    status: "blocked",
    owner: "ops",
    milestoneId: "m2-commercial-wiring",
    evidence: "Phase 12: not verified",
    internal: true,
  },
  {
    id: "sales-partners",
    title: "Partners & affiliate applications",
    description: "Open tracks with zero invented partner logos.",
    category: "sales",
    status: "done",
    owner: "sales",
    evidence: "/partners",
  },
  // Support
  {
    id: "sup-help",
    title: "Help Center + FAQ + billing help",
    description: "Customer Success surfaces live.",
    category: "support",
    status: "done",
    owner: "support",
  },
  {
    id: "sup-feedback",
    title: "Feedback portal with status + votes",
    description: "Store securely; no fake vote counts.",
    category: "support",
    status: "done",
    owner: "support",
    milestoneId: "m3-gtm-system",
    evidence: "/feedback + CustomerFeedback/FeedbackVote",
  },
  {
    id: "sup-email",
    title: "Support email routing (contact@)",
    description: "Resend / Forward Email for rtasstudio.com aliases.",
    category: "support",
    status: "done",
    owner: "ops",
  },
  // Business
  {
    id: "biz-legal",
    title: "Terms, Privacy, Refund policies",
    description: "Paddle MoR-required policy pages.",
    category: "business",
    status: "done",
    owner: "founder",
  },
  {
    id: "biz-roadmap",
    title: "Public roadmap published",
    description: "Honest Completed / In Progress / Planned / Under Review.",
    category: "business",
    status: "done",
    owner: "founder",
    milestoneId: "m3-gtm-system",
    evidence: "/roadmap",
  },
  {
    id: "biz-acquisition-dash",
    title: "Customer acquisition dashboard",
    description: "Real funnel aggregates or zeros — never invented traffic.",
    category: "business",
    status: "done",
    owner: "founder",
    internal: true,
    evidence: "/admin/acquisition + /admin/launch",
  },
];

export function checklistProgress(items: LaunchChecklistItem[] = LAUNCH_CHECKLIST) {
  const total = items.length;
  const done = items.filter((i) => i.status === "done").length;
  const inProgress = items.filter((i) => i.status === "in_progress").length;
  const blocked = items.filter((i) => i.status === "blocked").length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return { total, done, inProgress, blocked, pct };
}

export function publicChecklist(items: LaunchChecklistItem[] = LAUNCH_CHECKLIST) {
  return items.filter((i) => !i.internal);
}
