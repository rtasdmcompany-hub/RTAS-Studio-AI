# Support Operations

**Product:** RTAS Studio AI  
**Phase:** 13 · Sprint 6

---

## Channels

| Channel | Path | Notes |
|---------|------|-------|
| Help Center | `/help` | Searchable KB |
| Contact | `/help/contact` | Email / Discord |
| Tickets | `/tickets` | Authenticated; DB-backed |
| Feedback | `/feedback` | Bug / feature / CSAT / NPS |
| Admin queue | `/admin/tickets` | `x-rtas-admin-secret` |

## Ticket model

Fields: category, priority, subject, description, attachment metadata, status, ticket number, created/updated, replies, admin notes (internal).

**Statuses:** `open` · `in_progress` · `waiting_on_customer` · `resolved` · `closed`  
**Priorities:** `low` · `medium` · `high` · `urgent`  
**Categories:** account, billing, credits, video_generation, templates, ai_models, enterprise, api, security, technical, other

## RTA (honest, early-stage)

| Severity | Aim |
|----------|-----|
| Billing / access blockers | Same business day when staffed |
| Generation failures | Best-effort with job ID |
| Feature ideas | Logged via feedback; no fake roadmap SLAs |

Do not publish contractual SLAs until staffing and tooling can meet them.

## Security

- Customer APIs require session + email verified.  
- Admin APIs require `RTAS_ADMIN_SECRET`.  
- Admin notes and `isInternal` replies are never returned on customer ticket GET.  
- Attachment rows store metadata only (no binary in Postgres).  
- No seed tickets.

## API

- `GET/POST /api/support/tickets`  
- `GET/POST /api/support/tickets/[ticketId]`  
- `GET/PATCH /api/admin/tickets`
