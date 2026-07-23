# CRM Pipeline — RTAS Studio AI

**Phase:** 13 · Sprint 2  
**Implementation:** Prisma `EnterpriseLead` + admin UI at `/admin/enterprise`

## Stages

| Stage key | Label |
|-----------|-------|
| `new_lead` | New Lead |
| `qualified` | Qualified |
| `discovery` | Discovery |
| `demo_scheduled` | Demo Scheduled |
| `demo_completed` | Demo Completed |
| `proposal_sent` | Proposal Sent |
| `negotiation` | Negotiation |
| `closed_won` | Closed Won |
| `closed_lost` | Closed Lost |

Constants: `apps/web/src/lib/enterprise/pipeline.ts`

## Lead fields

- Status: `open` · `won` · `lost` · `nurturing`
- Priority: `low` · `medium` · `high` · `urgent`
- Owner, notes, tags, timeline, requirements
- `estimatedValueUsd` — optional; never auto-fabricated
- Activity history via `EnterpriseLeadActivity`

## Inbound mapping

| Source | Initial stage |
|--------|---------------|
| General inquiry / proposal / quote | `new_lead` |
| Demo / technical consultation / discovery | `demo_scheduled` |

## Admin operations

- Search: name, email, company, notes
- Filters: stage, status, priority, owner, tag
- PATCH stage/priority/owner/value/tags + append notes
- Widgets: Total, Qualified, Open Deals, Pipeline Value, Demos, Conversion %, Forecast  
  (Forecast = sum of open estimated values only — no invented win-rate multipliers)

## Alignment with Phase 11 docs

Process playbooks in `docs/business/sales/CRM-Workflow.md` remain the RevOps SOP. Product CRM uses a condensed stage set suitable for early enterprise GTM.
