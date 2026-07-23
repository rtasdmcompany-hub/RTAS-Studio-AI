/**
 * Phase 13 Sprint 2 — Trust / security posture for enterprise surfaces.
 * Claim only what the product supports; compliance = posture, not certification.
 */

export type EnterpriseTrustItem = {
  id: string;
  title: string;
  body: string;
  /** shipped = live control; posture = process/intent; roadmap = not shipped */
  maturity: "shipped" | "posture" | "roadmap";
};

export const ENTERPRISE_TRUST_ITEMS: EnterpriseTrustItem[] = [
  {
    id: "tls",
    title: "Encryption in transit",
    body: "TLS for web and API traffic. Secrets stay server-side and are never shipped to the browser.",
    maturity: "shipped",
  },
  {
    id: "auth",
    title: "Authenticated sessions",
    body: "NextAuth sessions with email verification gates on sensitive API paths.",
    maturity: "shipped",
  },
  {
    id: "rbac",
    title: "Role-based access (org)",
    body: "Organization/member roles exist in the multi-tenant model for collaborative workspaces.",
    maturity: "shipped",
  },
  {
    id: "admin",
    title: "Admin secret gating",
    body: "Operations and enterprise CRM admin APIs require RTAS_ADMIN_SECRET; surfaces are noindexed.",
    maturity: "shipped",
  },
  {
    id: "webhooks",
    title: "Payment webhook integrity",
    body: "Merchant-of-Record webhooks fail closed on invalid signatures; billing events are ledgered.",
    maturity: "shipped",
  },
  {
    id: "rate-limits",
    title: "Rate limiting",
    body: "Sensitive public forms and APIs apply IP-based rate limits to reduce abuse.",
    maturity: "shipped",
  },
  {
    id: "audit",
    title: "Audit logging",
    body: "Platform audit/activity models exist for enterprise security and collaboration events.",
    maturity: "shipped",
  },
  {
    id: "identity-policy",
    title: "Identity Preservation policy",
    body: "Authorized-only likeness workflows; unauthorized deepfake/face-swap misuse is not supported.",
    maturity: "shipped",
  },
  {
    id: "compliance",
    title: "Compliance-ready posture",
    body: "Legal pages, privacy controls, and security questionnaire readiness. Not a SOC 2 / ISO certification claim.",
    maturity: "posture",
  },
  {
    id: "sso",
    title: "Enterprise SSO / SCIM",
    body: "SSO/SCIM packaging is not a published self-serve feature; discuss in enterprise scoping.",
    maturity: "roadmap",
  },
];

export const ENTERPRISE_TRUST_MATURITY_LABELS: Record<
  EnterpriseTrustItem["maturity"],
  string
> = {
  shipped: "In product",
  posture: "Compliance posture",
  roadmap: "Roadmap",
};
