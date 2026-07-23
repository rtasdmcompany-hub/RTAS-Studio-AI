# Executive Dashboard

**Phase:** 13 · Sprint 7  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Surface:** `/admin/executive` (Overview tab)  
**Auth:** `x-rtas-admin-secret` = `RTAS_ADMIN_SECRET` (same as `/admin`)

---

## Purpose

CEO/CFO/CRO snapshot of live SaaS health. **All values are Prisma aggregates.** Zeros are valid. Gaps are labeled **N/A** — never fabricated for investor decks.

## Pricing inputs (verified)

| Plan | Price | Notes |
|------|------:|-------|
| Tester | $5 | One-time; **excluded from MRR** |
| Standard | $89/mo | Recurring |
| Premium | $249/mo | Recurring |

## Widgets

| Widget | Formula / source | Gap label |
|--------|------------------|-----------|
| MRR | `active Standard × 89 + active Premium × 249` | — |
| ARR | `MRR × 12` | — |
| New users | `User.createdAt` MTD / today | — |
| Active users | Users with GenerationJob or `updatedAt` in 30d | Proxy — not DAU sessions |
| Paid users | `subscriptionActive` or paid tier signal | — |
| Enterprise leads | `EnterpriseLead` count | — |
| Generations | `GenerationJob` total + today | — |
| Credit consumption | `sum(User.credits)`, `sum(creditsCharged)` | — |
| Revenue by plan | Active counts × list price | Tester MRR = $0 |
| Growth / conversion | signup→paid %, activation % | — |
| Churn | `paymentProvider` set + `subscriptionActive=false` | Approx, not MoR cohort |
| LTV | `paid ARPU ÷ churn rate` when churn > 0 | Else N/A |
| ARPU | MRR / paid actives | — |
| System health | queue, success %, failed 24h | GPU util = **N/A** |

## API

`GET /api/admin/executive` → `{ ok, kpis }`

## Integrity

Do not paste empty zeros into investor materials as “traction.” Label early-stage inventory honestly. Cross-link Phase 12 formula doc: [`../analytics/EXECUTIVE_DASHBOARD.md`](../analytics/EXECUTIVE_DASHBOARD.md).
