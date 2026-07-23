# Revenue Analytics

**Phase:** 13 · Sprint 7  
**UI:** `/admin/executive` → Revenue  
**APIs:**  
- `GET /api/admin/revenue-reports?period=daily|weekly|monthly|quarterly|yearly`  
- Existing RevOps: `GET /api/admin/revenue` · `/admin/revenue`

## Period compare

For each period, current vs previous window:

| Metric | Source |
|--------|--------|
| Signups | `User.createdAt` in window |
| Generations | `GenerationJob.createdAt` |
| Credits charged | `sum(creditsCharged)` |
| Ledger revenue USD | `sum(BillingTransaction.amountUsd)` where status completed/paid/success |
| Payment failures | failed/declined / eventType contains fail |

Δ% = `(current − previous) / previous` · if previous = 0 and current > 0 → `null` (shown as n/a).

## MRR vs ledger

| Concept | Definition |
|---------|------------|
| **MRR snapshot** | List-price × currently active Standard/Premium |
| **Ledger collected** | Historical webhook/ledger cash events (may be 0 early) |
| **Tester** | One-time estimate; never in MRR |

## Integrity

Empty periods return zeros. Do not backfill synthetic revenue.
