/**
 * Phase 13 Sprint 2 — Enterprise CRM pipeline constants & helpers.
 * Aligns with docs/business/sales/CRM-Workflow.md (simplified for product CRM).
 */

export const ENTERPRISE_PIPELINE_STAGES = [
  "new_lead",
  "qualified",
  "discovery",
  "demo_scheduled",
  "demo_completed",
  "proposal_sent",
  "negotiation",
  "closed_won",
  "closed_lost",
] as const;

export type EnterprisePipelineStage = (typeof ENTERPRISE_PIPELINE_STAGES)[number];

export const ENTERPRISE_STAGE_LABELS: Record<EnterprisePipelineStage, string> = {
  new_lead: "New Lead",
  qualified: "Qualified",
  discovery: "Discovery",
  demo_scheduled: "Demo Scheduled",
  demo_completed: "Demo Completed",
  proposal_sent: "Proposal Sent",
  negotiation: "Negotiation",
  closed_won: "Closed Won",
  closed_lost: "Closed Lost",
};

export const ENTERPRISE_LEAD_STATUSES = ["open", "won", "lost", "nurturing"] as const;
export type EnterpriseLeadStatus = (typeof ENTERPRISE_LEAD_STATUSES)[number];

export const ENTERPRISE_PRIORITIES = ["low", "medium", "high", "urgent"] as const;
export type EnterprisePriority = (typeof ENTERPRISE_PRIORITIES)[number];

export const ENTERPRISE_REQUEST_TYPES = [
  "demo",
  "technical_consultation",
  "discovery_call",
  "proposal",
  "meeting",
  "quote",
  "inquiry",
] as const;
export type EnterpriseRequestType = (typeof ENTERPRISE_REQUEST_TYPES)[number];

export const ENTERPRISE_DEMO_TYPES = [
  "book_demo",
  "technical_consultation",
  "discovery_call",
] as const;
export type EnterpriseDemoType = (typeof ENTERPRISE_DEMO_TYPES)[number];

export const ENTERPRISE_DEMO_TYPE_LABELS: Record<EnterpriseDemoType, string> = {
  book_demo: "Book Demo",
  technical_consultation: "Technical Consultation",
  discovery_call: "Discovery Call",
};

/** Commercial naming for enterprise GTM — maps to published SKUs honestly. */
export const ENTERPRISE_PLAN_INTERESTS = [
  "tester",
  "creator",
  "business",
  "enterprise",
] as const;
export type EnterprisePlanInterest = (typeof ENTERPRISE_PLAN_INTERESTS)[number];

export const OPEN_PIPELINE_STAGES: EnterprisePipelineStage[] = [
  "new_lead",
  "qualified",
  "discovery",
  "demo_scheduled",
  "demo_completed",
  "proposal_sent",
  "negotiation",
];

export const QUALIFIED_STAGES: EnterprisePipelineStage[] = [
  "qualified",
  "discovery",
  "demo_scheduled",
  "demo_completed",
  "proposal_sent",
  "negotiation",
  "closed_won",
];

export const DEMO_STAGES: EnterprisePipelineStage[] = [
  "demo_scheduled",
  "demo_completed",
];

export function isEnterprisePipelineStage(value: string): value is EnterprisePipelineStage {
  return (ENTERPRISE_PIPELINE_STAGES as readonly string[]).includes(value);
}

export function isEnterpriseLeadStatus(value: string): value is EnterpriseLeadStatus {
  return (ENTERPRISE_LEAD_STATUSES as readonly string[]).includes(value);
}

export function isEnterprisePriority(value: string): value is EnterprisePriority {
  return (ENTERPRISE_PRIORITIES as readonly string[]).includes(value);
}

export function stageImpliesStatus(stage: EnterprisePipelineStage): EnterpriseLeadStatus {
  if (stage === "closed_won") return "won";
  if (stage === "closed_lost") return "lost";
  return "open";
}

export function parseTags(raw: string | null | undefined): string[] {
  if (!raw?.trim()) return [];
  return raw
    .split(/[,|]/)
    .map((t) => t.trim())
    .filter(Boolean)
    .slice(0, 20);
}

export function serializeTags(tags: string[]): string {
  return tags
    .map((t) => t.trim())
    .filter(Boolean)
    .slice(0, 20)
    .join(", ");
}
