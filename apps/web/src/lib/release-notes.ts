/**
 * Structured release notes for the public changelog.
 * Source of truth: repo CHANGELOG.md + docs/RELEASE_NOTES.md (v1.0.0 only).
 * Do not invent prior releases.
 */

export type ReleaseNoteSection = {
  features?: string[];
  improvements?: string[];
  security?: string[];
  bugFixes?: string[];
  knownIssues?: string[];
};

export type ReleaseNote = {
  version: string;
  date: string;
  codename?: string;
  build?: string;
  summary: string;
  sections: ReleaseNoteSection;
};

/** Product version from apps/web/package.json — keep in sync when bumping. */
export const PRODUCT_VERSION = "1.0.0";

export const RELEASE_NOTES: ReleaseNote[] = [
  {
    version: "1.0.0",
    date: "2026-07-21",
    codename: "RC-2 Production Freeze",
    build: "20260721.1",
    summary:
      "First production freeze of the international AI video SaaS — Studio pipeline, auth, MoR billing scaffolding, admin ops, and production SEO.",
    sections: {
      features: [
        "Compose → Render → Publish studio with Identity Preservation and transparent credits (1 credit = 1 second)",
        "Email + Google authentication, email verification, and password reset via Resend",
        "Merchant-of-Record billing scaffolding (Paddle) with webhook-driven credit grants",
        "Admin operations dashboard with live database metrics",
        "Production SEO: canonical apex domain, robots, sitemap, Open Graph, JSON-LD",
        "Help Center, Feedback, Dashboard welcome flow, and SaaS documentation pack",
        "Forgot-password / reset-password with HMAC-signed tokens",
        "Live status probes on /status and web app manifest",
      ],
      improvements: [
        "Studio & Dashboard: first-time guidance, credits visibility, generation progress, library empty-state CTAs",
        "Clearer empty states and productization surfaces for international launch",
      ],
      security: [
        "Rate limits on auth, password reset, generate, and webhook paths",
        "Fail-closed Paddle webhook signature verification in production",
        "Email-verified API sessions, share URL allowlist, and upload validation",
        "www → apex permanent redirect; HSTS and security headers",
      ],
      bugFixes: [
        "Supabase pooler connectivity for Vercel serverless",
        "Resend domain verification path for rtasstudio.com",
        "Production robots.txt / sitemap.xml 404 (undeployed metadata routes)",
      ],
      knownIssues: [
        "Paddle live checkout requires seller-account checkout enablement",
        "Fal.ai live generation requires wallet balance",
        "CSP remains Report-Only pending Paddle/Google embed QA",
        "See docs/KNOWN_LIMITATIONS.md for the full accepted list",
      ],
    },
  },
];
