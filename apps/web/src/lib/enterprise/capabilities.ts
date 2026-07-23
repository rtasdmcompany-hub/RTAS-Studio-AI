/**
 * Phase 13 Sprint 2 — Enterprise capability matrix.
 * Labels are honest: available | roadmap | contact (scoping).
 */

export type EnterpriseCapabilityStatus = "available" | "roadmap" | "contact";

export type EnterpriseCapability = {
  id: string;
  title: string;
  description: string;
  status: EnterpriseCapabilityStatus;
};

export const ENTERPRISE_CAPABILITY_STATUS_LABELS: Record<
  EnterpriseCapabilityStatus,
  string
> = {
  available: "Available",
  roadmap: "Roadmap",
  contact: "Contact for scoping",
};

export const ENTERPRISE_CAPABILITIES: EnterpriseCapability[] = [
  {
    id: "saas",
    title: "Hosted SaaS studio",
    description:
      "Production studio at rtasstudio.com with credit metering and commercial downloads on paid tiers.",
    status: "available",
  },
  {
    id: "api",
    title: "Enterprise API access",
    description:
      "Developer/API surfaces exist for platform integrations; enterprise quotas and contracts are scoped per deal.",
    status: "contact",
  },
  {
    id: "integrations",
    title: "Custom integrations",
    description:
      "Workflow and tool integrations negotiated in proposal — not a self-serve marketplace of connectors.",
    status: "contact",
  },
  {
    id: "priority",
    title: "Priority rendering",
    description:
      "Queue priority and capacity commitments are discussed case-by-case; not a published SLA package today.",
    status: "contact",
  },
  {
    id: "am",
    title: "Dedicated account manager",
    description:
      "Named commercial contact for qualified enterprise deals during pilot and onboarding.",
    status: "contact",
  },
  {
    id: "sla",
    title: "Custom SLA",
    description:
      "Written uptime/response commitments are proposal items. We do not advertise a public 99.9% SLA.",
    status: "contact",
  },
  {
    id: "onboarding",
    title: "Custom onboarding",
    description:
      "Kickoff, policy walkthrough, and Identity Preservation guidance for brand/agency teams.",
    status: "available",
  },
  {
    id: "security",
    title: "Security posture review",
    description:
      "TLS, secret hygiene, webhook fail-closed, rate limits, verified sessions — questionnaire support on request.",
    status: "available",
  },
  {
    id: "private-deploy",
    title: "Private deployment",
    description:
      "Dedicated / private cloud or on-prem style deployment is not a self-serve product. Scoped only via sales.",
    status: "roadmap",
  },
  {
    id: "dedicated-gpu",
    title: "Dedicated GPUs",
    description:
      "We do not operate a marketed private GPU fleet for customers today. Capacity isolation is contact/roadmap.",
    status: "roadmap",
  },
  {
    id: "unlimited",
    title: "Unlimited workflows",
    description:
      "Credits remain metered (1 credit = 1 second). “Unlimited” packaging is not sold; volume plans are proposed.",
    status: "contact",
  },
  {
    id: "identity",
    title: "Authorized Identity Preservation",
    description:
      "Likeness workflows are intentional and policy-bound. Unauthorized identity use is not supported.",
    status: "available",
  },
];
