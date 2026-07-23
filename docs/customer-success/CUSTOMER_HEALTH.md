# Customer Health

**Route:** `/profile/health`  
**API:** `GET /api/user/health`  
**Lib:** `apps/web/src/lib/customer-success/customer-health.ts`

---

## Metrics (signed-in user only)

| Metric | Source |
|--------|--------|
| Account age | `User.createdAt` |
| Email verified | `User.emailVerified` |
| Subscription | `tier`, `subscriptionActive`, renews / expiry |
| Credits | `User.credits` |
| Projects | `Project` count |
| Videos | `GenerationJob` total + `COMPLETED` |
| Last login | `User.lastLoginAt` (set on successful sign-in) |
| Last generation | Latest `GenerationJob.createdAt` |
| Usage trend | Jobs in last 14 UTC days |
| Tickets | `SupportTicket` open / total |
| Risk | Rule-based from `churn-prevention.ts` |

## Admin posture

Ops can infer portfolio health from real admin metrics + ticket queue. Do not display fake aggregate CSAT/NPS dashboards until responses exist.

## Empty / null honesty

- `lastLoginAt` may be null for accounts created before Sprint 6.  
- Ticket counts are zero until the user opens a ticket.  
- Failed payment count is zero when no matching ledger rows exist.
