# Proposal System — RTAS Studio AI

**Phase:** 13 · Sprint 2  
**Admin UI:** `/admin/enterprise/proposals`  
**API:** `POST/GET /api/admin/enterprise/proposals`

## Template sections

1. Customer & requirements  
2. Proposed solution  
3. Timeline & onboarding  
4. Pricing & commercial terms (published rate card + deal-specific notes)  
5. Support & security posture  
6. Acceptance  

Generator: `apps/web/src/lib/enterprise/proposal.ts`  
Proposal IDs: `RSAI-ENT-YYYY-###`

## Export

- Live markdown preview (PDF-friendly plain structure)
- Download `.md`
- Optional persist to `EnterpriseProposal`
- Linking a CRM `leadId` appends activity and moves stage to `proposal_sent`

## Honesty

- Default copy includes published Tester/Standard/Premium prices only.
- Enterprise remains Contact Sales / proposal-scoped.
- Placeholders use brackets — operators must fill real discovery notes; never invent logos, certs, or ACV.
