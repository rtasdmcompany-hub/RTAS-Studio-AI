# Customer Analytics

**Phase:** 13 · Sprint 7  
**UI:** `/admin/executive` → Customer  
**API:** `GET /api/admin/customer-analytics`

## Metrics

| Metric | Definition |
|--------|------------|
| Registrations | Total / today / week / month `User` counts |
| Verified | `emailVerified=true` |
| Activation | Users with ≥1 `COMPLETED` GenerationJob; rate vs total users |
| Retention | 30d users with ≥1 GenerationJob (**proxy**) |
| Upgrades | Active Standard / Premium counts |
| Cancel | `paymentProvider` set + `subscriptionActive=false` |
| Sessions | **N/A** — no first-party session store |
| Projects / videos | `Project` count / completed jobs |
| Credits | Remaining sum, charged sum, zero-credit users |

## Gaps

- True cohort retention curves not implemented.
- Session / DAU requires vendor analytics or session table (not present).
- Upgrade events are inferred from current tier, not a dedicated upgrade ledger.
