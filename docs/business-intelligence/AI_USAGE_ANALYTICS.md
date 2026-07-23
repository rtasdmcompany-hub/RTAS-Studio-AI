# AI Usage Analytics

**Phase:** 13 · Sprint 7  
**UI:** `/admin/executive` → Generation  
**API:** `GET /api/admin/ai-usage?days=7..90` (default 30)

## Metrics

| Metric | Source |
|--------|--------|
| Generations / day | Bucket `GenerationJob.createdAt` |
| Avg render time | Mean `(completedAt − startedAt)` on completed jobs |
| GPU utilization | **N/A** — not measurable from app DB |
| Queue | Counts `QUEUED` + running statuses |
| Credits | `sum(creditsCharged)` in period |
| Popular models/templates | `groupBy(provider)` proxy (no `templateId` column) |
| Failure rate | failed / (completed + failed) |
| Retry rate | jobs with `retryCount > 0` / total period jobs |

## Gaps

- GPU / node util requires infra telemetry (Fal dashboard or host metrics).
- Template popularity needs a persisted template key on jobs.
- Not investor-grade real-time GPU fleet BI.
