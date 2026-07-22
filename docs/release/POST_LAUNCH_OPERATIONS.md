# Post-Launch Operations — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company  
**As-of:** 23 July 2026  
**Status note:** Written as the **operating runbook for when commercial launch is approved**. Current Sprint 10 decision is **NOT APPROVED** — execute pre-launch gates first ([`FINAL_GO_LIVE_REPORT.md`](./FINAL_GO_LIVE_REPORT.md)).

---

## 1. Operating model

| Role | Responsibility |
|------|----------------|
| Founder / CEO | MoR status, pricing truth, AUP, spend decisions |
| Ops Owner | Providers, incidents, backups, Domains/DNS |
| Support Owner | support@ / contact@ RTA; Help content accuracy |
| Eng Owner | Deploys, fail-closed auth/payments, observability |

Cadence: **daily** (pre-GO: Fal + Paddle + ready probes) · **weekly** commercial note · **monthly** scorecard refresh.

---

## 2. Daily health checks (15 minutes)

| Check | Method | Pass criteria |
|-------|--------|---------------|
| Web ready | `GET /api/ready` | `status: ready` |
| Web health | `GET /api/health` | `status: ok` |
| API health | `GET https://rtas-studio-ai-api.vercel.app/api/health` | `live_generation: true` when selling |
| Payments config | `GET /api/payments/config` | `provider: paddle`, non-null `clientToken` |
| Auth smoke | Open `/auth/login` | **200** |
| Support path | `/help/contact` | **200** |
| Fal balance | Fal dashboard | Sufficient credit for expected volume |
| Paddle | Seller dashboard | No unresolved domain/checkout blocks |

**If `live_generation: false`:** pause paid acquisition; show honest degrade messaging; top up Fal before resuming sales.

---

## 3. Incident severity

| SEV | Definition | Response |
|-----|------------|----------|
| SEV1 | Site down, auth broken, mass payment failure, AUP crisis | Immediate; founder + rollback |
| SEV2 | Generation blocked, webhook credit desync, email delivery outage | Same-day; pause ads if fulfillment broken |
| SEV3 | Copy bugs, `/contact` 404, soft naming | Scheduled fix |
| SEV4 | Polish / SEO enrichment | Backlog |

Comms: support@rtasstudio.com · update `/status` honestly · no fake “all systems certified” language.

---

## 4. Payments & credits ops

1. Prefer live Paddle transaction API with per-plan price IDs.  
2. Confirm `PADDLE_WEBHOOK_SECRET` set; never allow unsigned webhooks in production.  
3. On each plan change: one test purchase (Tester first) → ledger → Studio generate.  
4. Refunds: follow `/refund` + Paddle MoR process; log ticket.  
5. Weekly: reconcile Paddle export vs credit ledger (spreadsheet until finance system exists).  
6. **Never invent MRR** — only Paddle/book exports.

---

## 5. Generation & cost control

| Control | Action |
|---------|--------|
| Fal wallet | Auto-alert threshold (manual daily until automated) |
| Guard | Keep billing guard enabled |
| Fallback | Replicate only if configured & tested — do not claim dual-active without proof |
| Unit economics | Record Fal COGS/sec before margin claims |

---

## 6. Support RTA (early stage)

| Channel | Target |
|---------|--------|
| support@ / contact@ | Acknowledge ≤ 1 business day (early; improve when staffed) |
| Help center | Keep billing / troubleshooting aligned to Tester paid entry |
| Discord | Only if invite validated; else remove |

Escalate AUP / unauthorized likeness to Trust & Safety refusal SOP.

---

## 7. Change & release

1. Prefer small Vercel promotions.  
2. Smoke: `/`, `/pricing`, `/auth/login`, `/api/ready`, API `/api/health`.  
3. After payment/env changes: one checkout E2E.  
4. Rollback: previous production deployment.  
5. Never commit secrets; rotate on exposure.

---

## 8. Backups & continuity

| Asset | Practice |
|-------|----------|
| Postgres (Supabase) | Confirm PITR/backups enabled; quarterly restore drill |
| Env secrets | Password manager + Vercel env; dual-person access goal |
| DNS | Cloudflare change control; post-change SSL/email verify |
| Legal | Keep v1.1+ in sync with live pages |

Reference: [`../operations/BUSINESS_CONTINUITY_PLAN.md`](../operations/BUSINESS_CONTINUITY_PLAN.md), [`../operations/RISK_REGISTER.md`](../operations/RISK_REGISTER.md).

---

## 9. Metrics ritual (honest)

Track only measured values:

- Signups / verified emails  
- Tester checkouts started / completed (Paddle)  
- Credits granted vs generations completed  
- Support tickets / RTA  
- Fal spend vs revenue  

Blank is better than invented.

---

## 10. First 72 hours after true GO

1. Watch Fal balance hourly.  
2. Watch Paddle + webhook logs.  
3. Complete one full customer journey personally.  
4. Freeze non-essential deploys.  
5. Daily founder commercial note (5 bullets).

*Post-Launch Operations · prepared Sprint 10 · activate after Critical clearance*
