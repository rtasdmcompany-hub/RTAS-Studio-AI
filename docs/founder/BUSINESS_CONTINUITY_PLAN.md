# Business Continuity Plan — Founder Edition (Phase 13)

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (Pakistan)  
**Effective:** 23 July 2026 · Phase 13 Sprint 10  
**Class:** Continuity & disaster recovery (founder-operated)

**Extends (do not discard):** [`../operations/BUSINESS_CONTINUITY_PLAN.md`](../operations/BUSINESS_CONTINUITY_PLAN.md) · [`../BACKUP_RECOVERY.md`](../BACKUP_RECOVERY.md) · [`../BACKUP.md`](../BACKUP.md) · [`../RECOVERY.md`](../RECOVERY.md)

**Labeling:** RTO/RPO below are **operational goals**, not customer SLAs, unless a signed contract states otherwise.

---

## 1. Objectives

1. Restore customer-facing web availability after infra failure.  
2. Protect account, credit, and billing-state integrity.  
3. Limit generation downtime and communicate honestly when AI providers fail.  
4. Preserve domain, email, and MoR payment paths.  
5. Never fabricate uptime certifications or “all systems operational” when Critical paths are known down.

---

## 2. Critical business functions

| Function | Dependency | Priority |
|----------|------------|----------|
| Marketing + legal trust pages | Vercel + DNS | P1 |
| Auth / sessions | Vercel + DB + Google OAuth + email | P1 |
| Studio + credits | Vercel + Supabase + app logic | P1 |
| Video generation | Worker / Fal.ai (+ optional Replicate) | P1 when selling generation |
| Checkout / subscriptions | Paddle MoR (Lemon Squeezy adapter ready) | P1 when commercial live |
| Transactional email | Resend + DNS | P1 |
| Source / deploy | GitHub + Vercel | P1 |
| Edge / DNS | Cloudflare · registrar history Hostinger | P1 |

---

## 3. RTO / RPO goals

| Scenario | RPO goal | RTO goal |
|----------|----------|----------|
| Bad app deploy | N/A (Git) | **< 1 hour** promote prior Vercel deployment |
| Vercel platform outage | N/A | Vendor-dependent; status page honesty |
| Database loss/corruption | Provider backup window (often ≤24h; PITR if plan includes) | Hours–day after validated restore |
| Secrets compromise | N/A | Hours to rotate + redeploy |
| Fal / GPU outage | N/A | Degraded mode; optional Replicate if configured |
| Paddle outage / MoR hold | N/A | Commerce paused; no fake “billing operational” |
| DNS / domain failure | N/A | Minutes–hours (propagation) |
| Email (Resend) failure | N/A | Hours; publish alternate contact path |
| GitHub unavailable | Local clones | Pause new deploys; promote last good build |

---

## 4. Backup strategy

| Asset | Method | Notes |
|-------|--------|-------|
| Source | GitHub + protected mainline | Primary code recoverability |
| Postgres | Supabase automated backups / PITR | Monthly restore drill |
| Secrets | Vercel env + operator vault — **never git** | Export discipline |
| Redis / KV | Provider persistence; rebuildable cache | Ephemeral OK |
| User renders | Provider/storage URLs | May require re-generation |
| DNS | [`../RTASSTUDIO-COM-DNS.md`](../RTASSTUDIO-COM-DNS.md) | Restore from docs + registrar |

---

## 5. Disaster recovery playbooks

### 5.1 Infrastructure / hosting (Vercel)

1. Check Vercel status.  
2. Bad deploy only → Instant Rollback / promote last known-good production.  
3. Platform-wide → communicate delay; no alternate full host hot-standby claimed.  
4. After recovery → smoke `/api/health`, `/api/ready`, login, Studio shell.

### 5.2 Database

1. Confirm Supabase status + connection from Vercel.  
2. Prefer PITR / snapshot restore to staging validation first.  
3. Validate credit/subscription tables before cutting production DNS/app.  
4. Document restore timestamp and any data loss window.

### 5.3 Payment provider failure

1. Pause paid acquisition messaging.  
2. Check Paddle status + webhook delivery logs.  
3. Do **not** manually invent credits without audited ledger entry.  
4. If MoR holds account: communicate checkout unavailable; keep legal/support pages up.  
5. Lemon Squeezy adapter exists in code — cutover only with ENV + live E2E proof.

### 5.4 Email failure

1. Check Resend domain status + DNS DKIM/SPF/DMARC.  
2. Prefer known-good alias (`auth@` / `support@` / `contact@`).  
3. Temporary: publish alternate contact on `/status` and help pages.  
4. Re-test signup + password-reset inbox receipt before declaring recovered.

### 5.5 GPU / Fal generation failure

1. Confirm Fal balance, API status, worker health.  
2. Set honest status messaging (generation degraded).  
3. Optional Replicate fallback only if configured and tested.  
4. Prefer pause new paid signup marketing until one live render succeeds.  
5. Refunds: MoR-handled; document product defect path per `/refund`.

### 5.6 Incident response (IR) & communications

| Severity | Definition | Comms |
|----------|------------|-------|
| SEV-1 | Site down, auth broken, mass credit/payment corruption, data breach | Immediate founder; `/status` update; email affected users if PII risk |
| SEV-2 | Generation down for paid users, checkout failing, email delivery broken | `/status` + support auto-reply within 4h goal |
| SEV-3 | Partial degradation, single-vendor slowness | Log; weekly review |

**Comms rules:** Facts only. No fake “resolved” or SLA percentages. Link Help + MoR for billing.

---

## 6. Continuity contacts (fill privately; do not commit secrets)

| Role | Channel |
|------|---------|
| Founder / Ops Owner | Primary phone + email (vault) |
| Hosting | Vercel dashboard |
| Database | Supabase dashboard |
| MoR | Paddle seller + paddle.net buyer support |
| Email | Resend |
| DNS / edge | Cloudflare |
| Domain registrar | Hostinger / as documented |
| AI inference | Fal.ai (RunPod if used) |

---

## 7. Phase 13 reality notes

- As of Sprint 10 probes, **commerce E2E and live generation remain Open Critical gates**. Continuity plans assume those become live; until then, treat “Billing Operational” / “Generation Operational” status-page cards as **posture templates**, not proven SLAs.  
- `/sitemap.xml` **500** and GTM route **404**s are availability defects for SEO/GTM — fix before claiming full launch readiness.

---

## 8. Test cadence

| Test | Frequency | Evidence |
|------|-----------|----------|
| Health/ready monitors | Continuous / daily | Log |
| Vercel rollback drill | Quarterly | Timestamp + deploy ID |
| DB restore drill | Monthly preferred | Staging restore note |
| MoR webhook replay / sandbox | After any billing change | Ledger screenshot |
| Generation smoke | After Fal top-up / major release | Job ID + download |

---

*Phase 13 Sprint 10 — Founder BCP. Extends ops BCP; does not invent SLAs.*
