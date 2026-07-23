# Sales Funnel Architecture — RTAS Studio AI

**Phase:** 13 · Sprint 3  
**Product:** https://rtasstudio.com  
**Integrity:** Real system data only. No fabricated conversion rates, customers, or revenue.

---

## Journey map (Visitor → Customer Success)

| Stage | Surface | Primary CTA | Friction (audited) | Mitigation (Sprint 3) |
|-------|---------|-------------|--------------------|------------------------|
| Visitor | `/` homepage | Start creating | Auth gate on Studio | Honest CTA; pricing secondary |
| Interest | `/features`, `/showcase`, `/blog` | Start creating / Compare plans | Content→action gap | Standardized CTAs |
| Evaluate | `/pricing`, `/docs`, `/how-to-use` | Get Tester / Open Studio | “Free” misunderstanding | Explicit 0-credit / paid Tester copy |
| Lead | `/updates`, footer, `/enterprise`, `/demo` | Subscribe / Schedule demo | Capture gaps | `/api/leads/subscribe` + commercial CRM |
| Signup | `/auth/signup` | Create account | Email verify friction | Check-email flow (existing) |
| Activate | `/studio`, `/profile` checklist | Open Studio | 0 credits | Paywall + Retention Center |
| First video | Studio generate | Generate | Credit paywall | Context-aware plan compare |
| Paid | Checkout (Paddle) | Get Tester / Go Standard | MoR enablement ops | Ledger + RevOps visibility |
| Retain | Retention Center | Keep creating | Low-credit churn | Upgrade suggestions (no fake urgency) |
| Expand | Premium path | Compare Premium 4K | Unclear upgrade | Paywall + pricing matrix |
| Success | `/help`, feedback | Help Center | Support discoverability | Retention links + ticket logs |

---

## Funnel instrumentation

Analytics event names live in `apps/web/src/lib/analytics/events.ts` (Phase 13 additions: Lead Captured, Upgrade Prompt Shown, Lifecycle Stage, Retention Center Viewed, etc.).

**Rule:** Events may be zero. Never invent funnel percentages in UI or docs.

---

## Conversion CTA canon

Source: `apps/web/src/lib/conversion-ctas.ts`

- Prefer **Start creating** / **Get Tester** / **Open Studio**
- Never **Start Free** if it implies free generation credits
- Entry product = paid Tester ($5 / 30s / 5 days)

---

## Systems

| Capability | Route / module |
|------------|----------------|
| Lead subscribe | `POST /api/leads/subscribe` · `MarketingLead` |
| Commercial / enterprise | `POST /api/commercial/lead` · Enterprise CRM |
| RevOps | `/admin/revenue` · `GET /api/admin/revenue` |
| Lifecycle helpers | `apps/web/src/lib/customer-lifecycle.ts` |
| Retention UI | Dashboard `#retention-center` |
