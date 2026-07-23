# Business Alerts

**Phase:** 13 · Sprint 7  
**UI:** `/admin/executive` → Alerts  
**API:** `GET /api/admin/business-alerts?persist=0|1`  
**Engine:** `apps/web/src/lib/server/admin/business-alerts.ts`

## Model

Rule-based evaluation against live DB/log signals. **No invented incidents.**

When `persist` is not `0`, triggered warn/critical alerts are written to `SystemLog` with source `business.alert.<category>` (existing audit pattern).

## Rules

| ID | Category | Trigger |
|----|----------|---------|
| `payments.failures_24h` | payments | ≥1 failed billing tx (critical ≥5) |
| `errors.system_logs_24h` | errors | ≥10 error SystemLogs (critical ≥25) |
| `errors.job_failures_24h` | errors | ≥5 FAILED jobs/24h (critical ≥20) |
| `credits.low_inventory` | credits | sum(User.credits) ≤ 500 (critical ≤0) |
| `gpu_queue.depth` | gpu_queue | queued+running ≥15 (critical ≥50) |
| `infrastructure.maintenance` | infrastructure | active MaintenanceEvent |
| `infrastructure.db_ok` | infrastructure | info connectivity (not triggered when OK) |
| `security.warn_events_24h` | security | ≥20 auth/security warn+error logs |
| `enterprise.large_lead` | enterprise | open lead value ≥$5k or high/urgent priority |
| `downtime.success_rate` | downtime | success rate <90% when finished jobs exist |

## Out of scope

- PagerDuty / Slack webhook bus (not wired this sprint).
- Predictive anomaly ML.
