# Operations Manual — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Document class:** Enterprise operations  
**Effective:** 22 July 2026  
**Status:** Implemented operating cadence (founder-operated); not an externally audited SLA  

**Related:** [STANDARD_OPERATING_PROCEDURES.md](./STANDARD_OPERATING_PROCEDURES.md) · [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md) · [SUPPORT_OPERATIONS.md](./SUPPORT_OPERATIONS.md) · [docs/OPERATIONS.md](../OPERATIONS.md) · [docs/RECOVERY.md](../RECOVERY.md) · Phase 11 Sprint 1 [`business/PHASE11_SPRINT1_REPORT.md`](../../business/PHASE11_SPRINT1_REPORT.md)

---

## 1. Purpose

This manual defines how RTAS Studio AI is run day-to-day: monitoring rhythm, maintenance cycles, incident response, and escalation. It complements engineering runbooks under `docs/` and does not replace vendor dashboards or legal obligations.

---

## 2. Operating model

| Role | Accountability |
|------|----------------|
| **Founder / Ops Owner** | Final authority on production changes, vendor accounts, security incidents, customer communications |
| **Engineering (same operator today)** | Deployments, health checks, rollback, generation pipeline |
| **Support (same operator today)** | Inbox triage, billing handoffs to Paddle MoR, complaint handling |
| **Merchant of Record (Paddle)** | Card processing, tax, refunds under MoR; checkout/domain activation may still be pending — treat payment success as a live gate, not a assumed always-on state |

There is no separate 24×7 NOC. Severity-1 incidents are handled by the Ops Owner as soon as detected.

---

## 3. Daily operations

| Check | Method | Pass criteria |
|-------|--------|---------------|
| Site up | `GET https://rtasstudio.com/api/health` | `200` `{ status: "ok" }` |
| Ready for traffic | `GET https://rtasstudio.com/api/ready` | `200` ready (alert on `503`) |
| Vercel | Project → Deployments / Runtime logs | No unexplained failed production deploy; error spike investigated |
| Generation path | Spot-check Studio load; review Fal balance / error signals when generating | App loads; AI provider has balance |
| Payments | Paddle dashboard (webhooks / transactions when live) | No silent webhook failure pile-up when checkout is active |
| Email | Resend dashboard (bounces/complaints) | No sudden bounce/complaint spike |
| DNS / edge | Cloudflare + Vercel domain status | Domain resolves; SSL valid |
| Support inbox | `support@` / `contact@rtasstudio.com` | New messages acknowledged per [SUPPORT_OPERATIONS.md](./SUPPORT_OPERATIONS.md) |

**Daily log (lightweight):** date · health/ready · notable errors · open SEV tickets · vendor anomalies.

---

## 4. Weekly operations

| Task | Owner | Notes |
|------|-------|-------|
| Review Vercel bandwidth, function errors, and failed builds | Ops Owner | Correlate with recent deploys |
| Confirm Supabase backup / project health | Ops Owner | See [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md) |
| Dependency hygiene | Ops Owner | `npm audit` on lockfile; schedule upgrade PRs for high severity |
| Auth smoke | Ops Owner | Google OAuth login + email verification on production |
| Fal credit runway | Ops Owner | Avoid generation outage from zero balance |
| Support backlog | Ops Owner | Close or escalate aged threads |
| Change review | Ops Owner | List production deploys vs [CHANGE_MANAGEMENT.md](./CHANGE_MANAGEMENT.md) |
| Legal / AUP signals | Ops Owner | Flag Trust & Safety / AI Policy abuse reports |

---

## 5. Monthly operations

| Task | Notes |
|------|-------|
| Access review | Owner/admin emails, GitHub collaborators, Vercel/Supabase/Cloudflare members — see [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) |
| Secret hygiene | Confirm no secrets in git; rotate shared admin secrets if exposure risk rose |
| Restore drill (staging preferred) | Per [docs/BACKUP.md](../BACKUP.md) / [docs/BACKUP_RECOVERY.md](../BACKUP_RECOVERY.md) |
| Rate-limit / abuse review | Adjust if multi-instance or attack patterns appear |
| Vendor invoice & usage | Vercel, Supabase, Fal, Resend, Cloudflare, Forward Email, Hostinger (if billed) |
| Compliance spot-check | Public legal pages still v1.1; MoR statements still accurate — [COMPLIANCE_REGISTER.md](./COMPLIANCE_REGISTER.md) |
| Risk register refresh | Update statuses in [RISK_REGISTER.md](./RISK_REGISTER.md) |

---

## 6. Quarterly operations

| Task | Outcome |
|------|---------|
| Full vendor criticality review | Update [VENDOR_MANAGEMENT.md](./VENDOR_MANAGEMENT.md) |
| Business continuity tabletop | Walk one SEV1 scenario (app down, DB restore, payment outage) |
| Change-management retrospective | Emergency changes, rollback rate, hotfix quality |
| Support metrics review | Volume, severity mix, RTA attainment (manual until CRM) |
| Security governance review | MFA coverage, audit log sampling, env drift |
| Roadmap / commercial gate check | Honest status of Paddle checkout/domain path vs business roadmap |

---

## 7. Annual operations

| Task | Outcome |
|------|---------|
| Policy calendar | Re-approve legal suite versioning plan; confirm MoR and operator entity language |
| Disaster recovery exercise | Documented RTO/RPO goal vs observed result (goals, not contracted SLAs unless signed) |
| Vendor contract / ToS review | Material ToS changes for Paddle, Fal, Supabase, Vercel, Resend |
| Access attestation | Full inventory of privileged accounts |
| Operations manual revision | Bump this document; archive prior cadence assumptions |

**Certification note:** RTAS Studio AI does **not** claim ISO 27001, SOC 2, or GDPR certification. Annual work may *prepare* for future attestation; preparation ≠ certification.

---

## 8. Incident response

### 8.1 Severity

| Severity | Definition | Initial response goal |
|----------|------------|----------------------|
| **SEV1** | Site down, data loss risk, widespread payment failure, confirmed security breach | Immediate; continuous until mitigated |
| **SEV2** | Major feature degraded (generation, email, auth) for many users | Within 2 hours during working day; same-day mitigation plan |
| **SEV3** | Partial degradation or workaround exists | Next business day |
| **SEV4** | Cosmetic / low-impact | Backlog |

### 8.2 Response steps (all severities)

1. **Detect** — monitor, user report, vendor status, health/ready failure.  
2. **Triage** — assign severity; open incident note (time, symptom, impact).  
3. **Contain** — rollback deploy, disable bad config, rotate secret, rate-limit, or fail closed.  
4. **Diagnose** — Vercel logs, worker health, Supabase, Paddle webhooks, Resend, Fal, DNS.  
5. **Recover** — restore service; verify `/api/health`, `/api/ready`, login, Studio, checkout path if applicable.  
6. **Communicate** — acknowledge support tickets; status note if widespread.  
7. **Post-incident** — root cause, corrective action, update Risk Register within 7 days for SEV1/SEV2.

Detailed technical rollback: [docs/RECOVERY.md](../RECOVERY.md).  
Security-specific path: [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) and [docs/SECURITY.md](../SECURITY.md).  
Payment incidents: [STANDARD_OPERATING_PROCEDURES.md](./STANDARD_OPERATING_PROCEDURES.md) § Payment / MoR.

### 8.3 Decision rules

- Prefer **Vercel promote prior deployment** for bad app releases (fastest).  
- Prefer **fail closed** on missing webhook secrets or auth config in production.  
- Never store card PANs; payment disputes route through **Paddle** as Merchant of Record.  
- Do not invent “all systems certified” language in customer or investor replies during incidents.

---

## 9. Escalation path

| Level | Trigger | Action |
|-------|---------|--------|
| L1 | Customer email / Help Center | Support SOP; self-serve links |
| L2 | Confirmed product/infra defect | Ops Owner investigates logs + vendors |
| L3 | SEV1 or security/payment | Continuous work; vendor support tickets; optional temporary feature disable |
| External | MoR refunds, chargebacks, tax | Paddle support / dashboard |
| Legal / AUP abuse | Deepfake, impersonation, fraud reports | Trust & Safety process; preserve evidence; suspend abusing accounts when tools allow |

**Contacts (public):** support@rtasstudio.com · contact@rtasstudio.com  
**Production domain:** https://rtasstudio.com  

---

## 10. Maintenance windows

1. Announce expected impact (email or status note when audience is material).  
2. Snapshot / confirm DB backup posture.  
3. Deploy in low-traffic window when possible.  
4. Run smoke from [docs/RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md).  
5. Monitor `/api/ready` for 30–60 minutes post-change.

---

## 11. Health endpoints (production)

| Path | Meaning |
|------|---------|
| `/api/health` | Process alive |
| `/api/ready` | Critical config present |
| `/api/auth/config` | Public auth runtime flags |
| `/api/auth/email-config` | Email delivery mode |
| `/api/payments/config` | Payment provider public config |
| Worker `{FASTAPI_URL}/api/health` | Generation API alive |

---

## 12. Document control

| Field | Value |
|-------|-------|
| Owner | RTAS Digital Marketing Company — Ops Owner |
| Review cadence | Quarterly + after every SEV1 |
| Cross-sprint | Phase 11 Sprint 6 enterprise operations package |
