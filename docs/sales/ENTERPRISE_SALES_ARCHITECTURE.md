# Enterprise Sales Architecture — RTAS Studio AI

**Phase:** 13 · Sprint 2  
**Product:** https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company  

## Purpose

Implementation-backed enterprise sales infrastructure: public enterprise surfaces, inquiry/demo capture, Prisma CRM, admin pipeline, proposal generator, and honest trust UI.

## System map

```
/enterprise  →  inquiry form  →  POST /api/commercial/lead
/demo        →  demo booking  →  same API
                                    ├─ EnterpriseLead (+ Activity)  [Prisma]
                                    ├─ Admin email (Resend/SMTP)
                                    └─ Lead confirmation email
/admin/enterprise           →  GET/PATCH /api/admin/enterprise
/admin/enterprise/proposals →  POST /api/admin/enterprise/proposals
```

## Components

| Layer | Location |
|-------|----------|
| Public overview + pricing | `apps/web/src/app/enterprise/page.tsx` |
| Demo workflow | `apps/web/src/app/demo/page.tsx` |
| Lead form | `apps/web/src/components/commercial/CommercialLeadForm.tsx` |
| Capability / pricing / trust UI | `apps/web/src/components/enterprise/*` |
| CRM lib | `apps/web/src/lib/enterprise/*` |
| Prisma models | `EnterpriseLead`, `EnterpriseLeadActivity`, `EnterpriseProposal` |
| Admin CRM | `/admin/enterprise` |
| Proposals | `/admin/enterprise/proposals` |

## Auth & security

- Public forms: rate-limited (`commercial-lead:{ip}`).
- Admin APIs: `x-rtas-admin-secret` === `RTAS_ADMIN_SECRET` (same pattern as `/admin`).
- IP stored as SHA-256 hash only (`ipHash`).
- No fake seed leads. Empty CRM is the correct initial state.

## Honesty rules

- Enterprise tier: **Contact Sales** only — no fixed price.
- Creator = Standard ($89/mo); Business = Premium 4K ($249/mo).
- Capabilities labeled Available / Roadmap / Contact for scoping.
- Trust “compliance-ready” = posture, not SOC 2/ISO certification.
- Dashboard widgets show real counts or zero.

## Related docs

- [`CRM_PIPELINE.md`](./CRM_PIPELINE.md)
- [`ENTERPRISE_PRICING.md`](./ENTERPRISE_PRICING.md)
- [`DEMO_WORKFLOW.md`](./DEMO_WORKFLOW.md)
- [`PROPOSAL_SYSTEM.md`](./PROPOSAL_SYSTEM.md)
- [`ENTERPRISE_UI_AUDIT.md`](./ENTERPRISE_UI_AUDIT.md)
- Phase 11 process docs remain under `docs/business/sales/`
