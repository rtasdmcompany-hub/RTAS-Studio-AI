# Email Automation — RTAS Studio AI

**Phase:** 13 · Sprint 4  
**Integrity:** Templates and hooks only. Do not invent open/click rates.

## Registry

Source: `apps/web/src/lib/marketing/email-templates.ts`  
Layout: `apps/web/src/lib/marketing/email-layout.ts` (dark-mode friendly HTML shell)

| Template | Hook status | Trigger |
|----------|-------------|---------|
| Welcome | Live | Email verified |
| Verification | Live | Register / resend |
| Password Reset | Live | Forgot password |
| Video Ready | Live | `POST /api/notify/video-ready` |
| Payment Success | Live | Webhook activated / renewed |
| Billing Notifications | Live | Cancelled (and similar) |
| Subscription Expiry | Live (helper) | Call `sendSubscriptionExpiryEmail` |
| Enterprise Follow-up | Live | Commercial lead submit |
| Weekly Updates | Planned | Not scheduled |
| Feature Announcements | Planned | Ops campaign |
| Release Notes | Planned | Changelog publish |
| Newsletter | Planned | Marketing calendar |
| Payment Failure | Planned | Provider `payment_failed` when emitted |

## Send audit

`EmailSendLog` stores delivery status only (sent/failed). No fabricated opens/clicks.

## Ops UI

`/admin/marketing` — Email Marketing Center (admin secret).

## Related

- [`MARKETING_AUTOMATION.md`](MARKETING_AUTOMATION.md)
- Phase 12: [`EMAIL_MARKETING_SYSTEM.md`](EMAIL_MARKETING_SYSTEM.md)
