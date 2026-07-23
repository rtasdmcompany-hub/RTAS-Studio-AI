/**
 * Phase 13 Sprint 2 — Enterprise proposal markdown generator.
 * Export-ready structure; never invents customer logos, certs, or fake pricing.
 */

import {
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";

export type ProposalInput = {
  proposalNumber: string;
  dateIso?: string;
  customerName: string;
  customerContact?: string;
  customerEmail?: string;
  requirements?: string;
  solution?: string;
  timeline?: string;
  pricingNotes?: string;
  supportNotes?: string;
  acceptanceNotes?: string;
  validityDays?: number;
};

function section(title: string, body: string | undefined, fallback: string): string {
  const text = (body?.trim() || fallback).trim();
  return `## ${title}\n\n${text}\n`;
}

export function buildProposalMarkdown(input: ProposalInput): string {
  const date = input.dateIso
    ? new Date(input.dateIso)
    : new Date();
  const dateLabel = date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const validity = input.validityDays ?? 30;

  const header = [
    `# ${PRODUCT_NAME} — Enterprise Proposal`,
    "",
    `**Proposal ID:** ${input.proposalNumber}`,
    `**Date:** ${dateLabel}`,
    `**Validity:** ${validity} days from date above`,
    `**To:** ${input.customerName}`,
    input.customerContact ? `**Attention:** ${input.customerContact}` : null,
    input.customerEmail ? `**Email:** ${input.customerEmail}` : null,
    `**From:** RTAS Digital Marketing Company — ${PRODUCT_NAME}`,
    `**Product URL:** https://rtasstudio.com`,
    "",
    "---",
    "",
  ]
    .filter((line): line is string => line !== null)
    .join("\n");

  const requirements = section(
    "1. Customer & requirements",
    input.requirements,
    `[Describe ${input.customerName}'s objectives, workflows, volume hypothesis, and constraints. Do not invent metrics.]`
  );

  const solution = section(
    "2. Proposed solution",
    input.solution,
    `${PRODUCT_NAME} — AI video studio for text/image-driven generation oriented to commercials, music videos, animation, and brand storytelling.

**Included (default pilot framing)**
- Access at https://rtasstudio.com
- Seconds-based credits (1 credit = 1 second)
- Authorized Identity Preservation only
- Support via contact@rtasstudio.com / support@rtasstudio.com
- Live legal policies (Terms, Privacy, Refund, Cookies, AI Policy, Trust & Safety)

**Out of scope unless separately agreed**
- Guaranteed cinematic output on every generation
- Unauthorized third-party likeness workflows
- Public SOC 2 / ISO certification claims
- Dedicated private GPU fleet as a self-serve SKU`
  );

  const timeline = section(
    "3. Timeline & onboarding",
    input.timeline,
    "Pilot term: [30 / 60 / 90] days. Kickoff session, mid-pilot checkpoint, final review. Named customer admin required."
  );

  const pricing = section(
    "4. Pricing & commercial terms",
    input.pricingNotes,
    `**Published rate card (verified — not invented)**

| Plan | Commercial name | Price |
|------|-----------------|-------|
| Tester | Tester | USD $${TESTER_PRICE_USD} evaluation |
| Standard | Creator (enterprise naming) | USD $${STANDARD_PRICE_USD} / month |
| Premium 4K | Business (enterprise naming) | USD $${PREMIUM_PRICE_USD} / month |
| Enterprise | Enterprise | Contact sales / proposal — **no fixed public price** |

This proposal configuration: [seats, seconds, services, payment via Paddle MoR].
Volume discounts and custom terms are written here only when agreed — never fabricated in public copy.`
  );

  const support = section(
    "5. Support & security posture",
    input.supportNotes,
    `Support via published channels. Security posture includes TLS, secret hygiene, webhook integrity, rate limits, and admin gating.

**Compliance-ready** describes questionnaire and policy posture — not SOC 2 / ISO certification unless independently attested.`
  );

  const acceptance = section(
    "6. Acceptance",
    input.acceptanceNotes,
    `By accepting this proposal, ${input.customerName} confirms authorized use of any likeness/media provided, and agrees to ${PRODUCT_NAME} Terms and Privacy Policy.

**Accepted by**

| | Customer | RTAS Digital Marketing Company |
|--|----------|--------------------------------|
| Name | | |
| Title | | |
| Date | | |
| Signature | | |`
  );

  return [header, requirements, solution, timeline, pricing, support, acceptance].join(
    "\n"
  );
}

export function nextProposalNumber(existingCount: number, year = new Date().getFullYear()): string {
  const seq = String(Math.max(1, existingCount + 1)).padStart(3, "0");
  return `RSAI-ENT-${year}-${seq}`;
}
