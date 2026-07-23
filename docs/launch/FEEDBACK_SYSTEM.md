# Feedback System

**Phase:** 13 · Sprint 9  
**Public portal:** `/feedback`  
**APIs:** `GET/POST /api/feedback`, `POST /api/feedback/[id]/vote`  
**Persistence:** `CustomerFeedback` + `FeedbackVote` (Prisma)

---

## Capabilities

| Capability | Behavior |
|------------|----------|
| Feature / bug / suggestion / feedback / other | Validated POST |
| CSAT 1–5 | Required on submit |
| Title + message | Stored; public board truncates long messages |
| Status | `received` → `under_review` → `planned` → `in_progress` → `shipped` / `closed` |
| Votes | One per voterKey (user id or hashed IP); `voteCount` increments only on new votes |
| Email notify | Best-effort via Resend/SMTP when configured |
| Audit | `systemLog` source `product.feedback` |

---

## Integrity

- **No seed / fake votes.** Empty board is valid.
- Email and IP hashes are not exposed on the public GET board.
- Rate limits: 10 submissions / hour / IP; 60 votes / hour / IP.
- If DB unavailable and email unavailable → 503 with support email.

---

## Admin workflow

1. Review new `CustomerFeedback` rows (status `received`).
2. Update `status` in DB/admin tooling (no public self-status edits).
3. Set `isPublic=false` to hide sensitive reports.
4. Correlate with Support tickets (`SupportTicket`) when a signed-in user needs 1:1 help.

---

## Migration

`apps/web/prisma/migrations/20260723_feedback_portal_votes/migration.sql`
