/**
 * Phase 13 Sprint 9 — Public product roadmap (honest).
 * View-only source for /roadmap. No invented ship dates as guarantees.
 */

import type { RoadmapItem } from "./types";

export const PUBLIC_ROADMAP: RoadmapItem[] = [
  {
    id: "rw-studio-core",
    title: "Compose → Render → Publish Studio",
    summary:
      "Core generation workflow with transparent second-based credits and Identity Preservation controls.",
    status: "completed",
    area: "Product",
  },
  {
    id: "rw-auth-billing",
    title: "Auth, email verification & MoR billing scaffolding",
    summary:
      "Credentials + Google auth, Resend email flows, Paddle Merchant of Record checkout scaffolding with webhook credit grants.",
    status: "completed",
    area: "Platform",
  },
  {
    id: "rw-help-seo",
    title: "Help Center, SEO, status & legal policies",
    summary:
      "Customer Success surfaces, sitemap/robots, trust & refund policies for international SaaS launch.",
    status: "completed",
    area: "Go-to-market",
  },
  {
    id: "rw-enterprise-crm",
    title: "Enterprise CRM & demo pipeline",
    summary: "Lead capture, pipeline stages, and commercial forms on /enterprise and /demo.",
    status: "completed",
    area: "Sales",
  },
  {
    id: "rw-partners",
    title: "Partners & affiliate application tracks",
    summary: "Open partnership tracks without fabricated logos or invented commission results.",
    status: "completed",
    area: "Growth",
  },
  {
    id: "rw-gtm-center",
    title: "Global GTM Launch Center",
    summary:
      "Launch checklist, campaign plans, asset library, acquisition dashboard, and executive readiness.",
    status: "completed",
    area: "Go-to-market",
  },
  {
    id: "rw-feedback-portal",
    title: "Feedback portal with votes & status",
    summary: "Feature requests, bugs, and suggestions stored securely with real vote counts only.",
    status: "completed",
    area: "Customer Success",
  },
  {
    id: "rw-live-paddle",
    title: "Live Paddle purchase → credits verification",
    summary:
      "End-to-end proof that paid checkout grants credits in production before scaling paid ads.",
    status: "under_review",
    area: "Commerce",
  },
  {
    id: "rw-live-generation",
    title: "Live Fal generation clearance",
    summary: "Confirm funded provider wallet and successful production renders.",
    status: "under_review",
    area: "Infrastructure",
  },
  {
    id: "rw-analytics-vendors",
    title: "GA4 / PostHog vendor sinks",
    summary:
      "Architecture and consent ready; vendor SDKs marked Ready for Integration until keys are live.",
    status: "planned",
    area: "Analytics",
  },
  {
    id: "rw-paid-ads",
    title: "Google Ads & Meta Ads first campaigns",
    summary: "Campaign structures exist; spend starts only after conversion tracking is verified.",
    status: "planned",
    area: "Growth",
  },
  {
    id: "rw-product-hunt",
    title: "Product Hunt launch day",
    summary: "Gallery, maker comment, and hunter plan — no fabricated rankings beforehand.",
    status: "planned",
    area: "Go-to-market",
  },
  {
    id: "rw-api-public",
    title: "Public developer API GA",
    summary: "Developers surface exists; broader public API GA remains planned.",
    status: "planned",
    area: "Platform",
  },
  {
    id: "rw-csp-enforce",
    title: "CSP enforcement mode",
    summary: "Move Content-Security-Policy from Report-Only after Paddle/Google embed QA.",
    status: "planned",
    area: "Security",
  },
];

export const ROADMAP_STATUS_LABEL: Record<RoadmapItem["status"], string> = {
  completed: "Completed",
  in_progress: "In Progress",
  planned: "Planned",
  under_review: "Under Review",
};

export function roadmapByStatus(status: RoadmapItem["status"]) {
  return PUBLIC_ROADMAP.filter((i) => i.status === status);
}
