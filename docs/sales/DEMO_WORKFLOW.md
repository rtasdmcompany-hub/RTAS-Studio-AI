# Demo Workflow — RTAS Studio AI

**Phase:** 13 · Sprint 2  
**Public route:** `/demo`  
**API:** `POST /api/commercial/lead` with `kind: "demo"`

## Session types

| `demoType` | Label | Intent |
|------------|-------|--------|
| `book_demo` | Book Demo | Product walkthrough |
| `technical_consultation` | Technical Consultation | Security/API/deploy scoping |
| `discovery_call` | Discovery Call | Commercial/use-case discovery |

## Flow

1. Prospect submits form (name, business email, company, role, session type, plan interest, context).
2. Lead persisted to `EnterpriseLead` when `DATABASE_URL` is configured; stage → `demo_scheduled`.
3. Activity `demo_booked` recorded.
4. If email configured (Resend/SMTP):
   - Admin notification → `contact@rtasstudio.com`
   - Confirmation email → prospect
5. If DB unavailable and email unavailable → honest 503 with mailto fallback.

## Related

- Enterprise inquiry (non-demo): `/enterprise#contact`
- CRM follow-up: `/admin/enterprise`
