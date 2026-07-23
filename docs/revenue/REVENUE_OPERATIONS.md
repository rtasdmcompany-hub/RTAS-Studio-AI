# Revenue Operations — RTAS Studio AI

**Phase:** 13 · Sprint 3  
**Admin:** `/admin/revenue` (secret-gated via `x-rtas-admin-secret`)  
**API:** `GET /api/admin/revenue`

---

## Metrics (real aggregates only)

| Metric | Source |
|--------|--------|
| New Signups (today / 7d / month / total) | `User.createdAt` |
| Verified | `User.emailVerified` |
| Free (unpaid) | `tier=free` AND `subscriptionActive=false` |
| Paid signals | Active sub OR paid tier |
| MRR | `standard_active × $89` + `premium_active × $249` |
| ARR | `MRR × 12` |
| Tester one-time (est.) | `tester_count × $5` — **excluded from MRR** |
| Ledger collected | Sum `BillingTransaction.amountUsd` (completed/paid/success) |
| Subscription status | Active / inactive + tier groupBy |
| Credit usage | Remaining credits, job `creditsCharged`, zero-credit users |
| Top plans | Counts + MRR contribution |
| Recent transactions | Latest `BillingTransaction` rows |
| Support tickets | `SystemLog` feedback + commercial + marketing leads |

Zeros are valid. Never fabricate.

---

## Implementation

- `apps/web/src/lib/server/admin/revenue-metrics.ts`
- `apps/web/src/components/admin/RevenueOpsDashboardClient.tsx`
- Link from `/admin` → Revenue ops

---

## Rollback

Remove `/admin/revenue` route + API; ops dashboard remains. Metrics module is read-only.
