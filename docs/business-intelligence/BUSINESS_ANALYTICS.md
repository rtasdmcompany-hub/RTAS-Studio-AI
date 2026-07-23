# Business Analytics Center

**Phase:** 13 · Sprint 7  
**Surface:** `/admin/executive` tabs  
**API:** `GET /api/admin/business-analytics`

## Tabs

| Tab | Content | Primary sources |
|-----|---------|-----------------|
| Revenue | MRR/ARR, ledger, period compare | `User` tiers, `BillingTransaction` |
| Customer | Registrations, activation, retention proxy | `User`, `GenerationJob`, `Project` |
| Usage | Credits, jobs, projects | Same |
| Generation | AI usage slice | `GenerationJob` |
| Infrastructure | Queue, success, DB | Jobs + connectivity |
| Support | Feedback / lead log counts | `SystemLog`, `MarketingLead` |
| Enterprise | Pipeline KPIs | `EnterpriseLead` via CRM helpers |
| Marketing | Marketing + newsletter | `MarketingLead`, `NewsletterSubscriber` |
| Reports | CSV / HTML downloads | Report builders |
| Alerts | Rule-based business alerts | Threshold evaluators |

## Design notes

- Reuses RTAS admin design tokens (`text-ds-*`, `@rtas/ui` Card/Button/Alert).
- Shared nav links Ops · Executive BI · RevOps · Enterprise · Marketing · Tickets.
- Not a real-time streaming warehouse — on-demand query on refresh.

## Gaps

- No dedicated support-ticket warehouse beyond logs/marketing tables (see `/admin/tickets` if present).
- No ad-spend / CAC import.
- Product analytics events (`@/lib/analytics`) sink to structured logs, not a first-party warehouse table.
