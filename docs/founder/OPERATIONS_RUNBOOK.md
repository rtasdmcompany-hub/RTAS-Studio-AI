# Operations Runbook — RTAS Studio AI

**Product:** https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company  
**Phase:** 13 · Sprint 10 · 23 July 2026  

**Extends:** [`../operations/OPERATIONS_MANUAL.md`](../operations/OPERATIONS_MANUAL.md) · [`../operations/STANDARD_OPERATING_PROCEDURES.md`](../operations/STANDARD_OPERATING_PROCEDURES.md) · [`../operations/SUPPORT_OPERATIONS.md`](../operations/SUPPORT_OPERATIONS.md) · [`../release/POST_LAUNCH_OPERATIONS.md`](../release/POST_LAUNCH_OPERATIONS.md)

---

## 1. Monitoring

| Signal | Endpoint / place | Alert if |
|--------|------------------|----------|
| Liveness | `GET https://rtasstudio.com/api/health` | Non-200 or `status` ≠ `ok` |
| Readiness | `GET https://rtasstudio.com/api/ready` | 503 / not `ready` |
| Observability flags | health JSON `observability.sentry` / `analytics` | Both false → blind ops (known as of 23 Jul 2026) |
| Status UI | `/status` | Must match reality (do not leave “All systems operational” if Fal/billing known broken) |
| Hosting | Vercel → Deployments / Logs | Failed prod deploy; error spike |
| DB | Supabase | Connection / storage alerts |
| MoR | Paddle webhooks / transactions | Delivery failures when checkout live |
| Email | Resend | Bounce/complaint spike |
| AI | Fal dashboard + Studio errors | Zero balance; elevated job failures |

**Note:** Public `/api/health` (prod) currently returns process liveness + observability flags only — it does **not** expose Fal `live_generation`. Use admin/Studio paths + Fal dashboard for generation truth.

---

## 2. Health-check procedure (5 minutes)

1. Open `/api/health` → expect `ok`.  
2. Open `/api/ready` → expect `ready`.  
3. Open `/` and `/pricing` → expect 200; pricing shows $5 / $89 / $249.  
4. Open `/auth/login` → expect 200.  
5. Open `/studio` while logged out → expect auth gate (redirect/login).  
6. Open `/help/contact` → expect 200.  
7. Optionally `GET /api/payments/config` → note provider + whether `clientToken` present.  
8. Log result in daily checklist.

**Known defects to re-check until Cleared:** `/contact` 404 · `/sitemap.xml` 500 · `/enterprise` `/beta` `/partners` `/affiliate` 404.

---

## 3. Support triage

| Severity | Examples | Action |
|----------|----------|--------|
| SEV-1 | Total outage, auth down, payment/credit corruption, suspected breach | Page founder; update `/status`; preserve logs |
| SEV-2 | Cannot generate with paid credits; checkout failing; email verification broken | Acknowledge ≤4h goal; work Fal/MoR/Resend |
| SEV-3 | Single-user confusion, naming questions, feature request | Help docs + email; backlog |

**Channels:** `support@rtasstudio.com` · `contact@rtasstudio.com` · feedback mailto · Discord (community only; billing via email).  
**Billing refunds:** Paddle MoR / paddle.net — RTAS does not reverse cards.

Templates: [`../operations/SUPPORT_OPERATIONS.md`](../operations/SUPPORT_OPERATIONS.md).

---

## 4. Release procedure

1. Change merged to main (or release branch per repo practice).  
2. Confirm CI / build green when available.  
3. Deploy via Vercel production.  
4. Smoke: health, ready, homepage, pricing, login, help/contact.  
5. If billing/generation touched: one auth’d checkout or generation smoke **before** announcing.  
6. Note deploy ID + time in change log.

**Do not** market new GTM URLs until they return 200 on production.

---

## 5. Bug-fix procedure

1. Reproduce (prod vs preview).  
2. Classify severity.  
3. Prefer smallest safe fix; match existing conventions.  
4. Add regression note if payment/credits/auth involved.  
5. Deploy + smoke.  
6. Reply to reporter with honest status.

---

## 6. Rollback procedure

1. Vercel → Production → prior deployment → **Promote** / Instant Rollback.  
2. Confirm health + ready.  
3. If DB migration caused issue: follow [`../RECOVERY.md`](../RECOVERY.md) — do not “fix forward” blindly on credits.  
4. Communicate on `/status` if user-visible.  
5. Root-cause before re-deploying the bad change.

**RTO goal:** < 1 hour for bad frontend/app deploy.

---

## 7. Escalation

| Layer | Who | When |
|-------|-----|------|
| L1 | Founder / Ops Owner | All SEV today (single-operator) |
| Vendor | Vercel / Supabase / Paddle / Fal / Resend / Cloudflare | After local config ruled out |
| Legal / privacy | Counsel + `legal@` / `privacy@` | Breach, MoR dispute, AUP edge |
| MoR trust | Paddle account manager / AUP | Chargeback abuse, prohibited content |

No 24×7 NOC is claimed. SEV-1 is “as soon as detected.”

---

## 8. Payment ops (when live)

| Step | Action |
|------|--------|
| Config | `/api/payments/config` shows intended provider |
| Checkout | Auth’d session; fail-closed 503 if price IDs missing (correct) |
| Webhook | Unsigned → 401; signed → ledger + credits |
| Verify | Receipt + dashboard credits + DB ledger row |
| Failure | Pause ads; do not manually invent balances |

Architecture: [`../payments/PAYMENT_ARCHITECTURE.md`](../payments/PAYMENT_ARCHITECTURE.md).

---

## 9. Generation ops

| Step | Action |
|------|--------|
| Pre-flight | Fal balance + key present |
| Smoke | One short Tester-tier render after top-up / release |
| Block | If provider billing blocks spend, stop selling generation until Cleared |
| Fallback | Replicate only if configured and tested |

---

## 10. Escalation contacts (store privately)

Founder vault: phones, recovery codes, vendor logins — **never commit**.

---

*Phase 13 Sprint 10 — Operations Runbook.*
