# Marketing Automation — RTAS Studio AI

**Phase:** 13 · Sprint 4  
**Product:** https://rtasstudio.com

## Architecture

```text
Events (auth, billing, leads, video-ready)
    → Template registry + branded HTML layout
    → Resend / SMTP mailer
    → EmailSendLog (delivery only)

Admin Marketing Center (/admin/marketing)
    → Segments (real User / lead counts)
    → Campaigns (DB or Planned stubs)
    → Metrics: 0 or “Not connected” until ESP webhooks
```

## Surfaces

| Surface | Path |
|---------|------|
| Email Marketing Center | `/admin/marketing` |
| API | `/api/admin/marketing` |
| Newsletter subscribe | `/api/newsletter/subscribe` |
| Engagement Center | `/engage` |
| Referral | `/referral` |
| Notification prefs | `/profile/notifications` |

## ESP metrics policy

Resend open/click/bounce webhooks are **not connected**. Campaign dashboard must show **Not connected** or **0** — never invented rates.

## Migration

`apps/web/prisma/migrations/20260723_marketing_automation/migration.sql`

Apply in production before relying on newsletter / referral / send logs.
