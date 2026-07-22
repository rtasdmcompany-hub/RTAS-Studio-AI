# Business Continuity Plan — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Classification:** Continuity & disaster recovery (founder-operated)  

**Labeling rule:** RTO/RPO figures below are **operational goals** unless a signed customer SLA or vendor contract states otherwise. They are **not** contracted SLAs for end customers today.

**Related:** [docs/BACKUP_RECOVERY.md](../BACKUP_RECOVERY.md) · [docs/BACKUP.md](../BACKUP.md) · [docs/RECOVERY.md](../RECOVERY.md) · [VENDOR_MANAGEMENT.md](./VENDOR_MANAGEMENT.md) · [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md)

---

## 1. Objectives

1. Restore customer-facing web availability after infrastructure failure.  
2. Protect account, credit, and billing-state integrity.  
3. Limit generation downtime and clarify status when AI providers fail.  
4. Preserve domain, email, and MoR payment paths.  
5. Communicate honestly — no fabricated certification or uptime claims.

---

## 2. Critical business functions

| Function | Dependency | Continuity priority |
|----------|------------|---------------------|
| Marketing site + legal trust pages | Vercel + DNS | P1 |
| Auth / sessions | Vercel + DB + Google OAuth + email | P1 |
| Studio + credits | Vercel + Supabase + app logic | P1 |
| Video generation | FastAPI worker + Fal.ai (+ optional Replicate) | P1 for paid generation |
| Checkout / subscriptions | Paddle MoR (checkout may be pending activation) | P1 when live; treat as gated if not approved |
| Transactional email | Resend + DNS auth | P1 |
| Inbound email | Forward Email + DNS | P2 |
| Source control / deploy | GitHub + Vercel | P1 |
| Edge / DNS | Cloudflare (primary path) · Hostinger (domain history) | P1 |

---

## 3. RTO / RPO goals (not customer SLAs)

| Scenario | RPO goal | RTO goal | Basis |
|----------|----------|----------|-------|
| App bad deploy | N/A (code in Git) | **< 1 hour** via Vercel promote | Ops goal — [docs/RECOVERY.md](../RECOVERY.md) |
| Full Vercel outage | N/A | Dependent on vendor; status page tracking | External |
| Database corruption / loss | Provider backup window (often **≤ 24h** on common tiers; PITR if plan includes it) | Hours–day depending on restore validation | Ops goal — plan-dependent |
| Secrets compromise | N/A | Hours to rotate + redeploy | Ops goal |
| Fal.ai generation outage | N/A (jobs may fail; media retention provider-side) | Degraded mode until provider recovers; optional Replicate if configured | Ops goal |
| Paddle payment outage / MoR hold | N/A | Degraded commerce until vendor/approval restores | External + commercial gate |
| DNS / domain failure | N/A | Minutes–hours (propagation) | Ops goal |
| Email (Resend) failure | N/A | Hours; manual alternate contact path | Ops goal |
| GitHub unavailable | Local clones | Deploy may pause; promote last Vercel build if needed | Ops goal |

---

## 4. Backup strategy

| Asset | Method | Notes |
|-------|--------|-------|
| Application source | GitHub remotes + protected mainline | Primary recoverability for code |
| Postgres | Supabase automated backups / PITR (plan-dependent) | Validate monthly restore drill |
| Env / secrets | Vercel project env + operator vault (not git) | Export discipline; never commit |
| Redis / KV | Provider persistence; treat as ephemeral cache | Rebuildable |
| User renders | Provider/storage URLs; retention per Fal/storage | May require re-generation |
| DNS | Documented zone (`docs/RTASSTUDIO-COM-DNS.md`) | Restore from documentation + registrar |

---

## 5. Failure playbooks

### 5.1 Cloud / hosting (Vercel)

1. Check Vercel status.  
2. If only our deploy: promote last known-good production deployment.  
3. If platform-wide: communicate delay; no alternate full host hot-standby is claimed today.  
4. After recovery: smoke health/ready/login/Studio.

### 5.2 AI generation (Fal.ai / worker)

1. Confirm worker health and Fal status/balance.  
2. If Fal down and Replicate configured: enable documented fallback path.  
3. If no fallback: mark generation degraded; preserve credits policy fairness (do not silently charge for failed provider jobs — follow product refund/credit rules).  
4. Resume when provider recovers; clear backlog messaging.

### 5.3 Payment (Paddle MoR)

1. Verify whether checkout is **live vs pending approval** — honest status to customers.  
2. Check webhooks and payment config endpoint.  
3. Pause marketing of paid conversion if MoR blocks domain/checkout.  
4. Route refunds/chargebacks through Paddle; keep ledger notes for credit adjustments.

### 5.4 Database (Supabase)

1. Stop writes if corruption suspected (feature freeze / maintenance messaging).  
2. Restore via Supabase backups/PITR to a **validation** database first when possible.  
3. Cut over connection strings only after Prisma/schema validation.  
4. Verify auth, credits, and webhook idempotency assumptions.

### 5.5 Domain / DNS

1. Restore records from DNS documentation.  
2. Confirm Vercel domain + SSL.  
3. Confirm Resend SPF/DKIM and Forward Email routing.  
4. Account for TTL propagation in RTO expectations.

### 5.6 Email

1. Resend outage: use alternate operator mailbox for urgent support; delay non-critical mail.  
2. DNS auth break: restore records before bulk send.  
3. Forward Email failure: temporary public contact path via verified alternate if required.

---

## 6. Continuity roles

| Role | Duty |
|------|------|
| Ops Owner | Declare incident, approve restore, customer messaging |
| Engineering (same operator) | Execute rollback/restore |
| MoR (Paddle) | Payment continuity / refunds |
| Vendors | Platform restoration per their status |

---

## 7. Communication template (internal)

- Incident ID / start time  
- Impacted functions (auth, pay, generate, email, DNS)  
- Current hypothesis  
- Customer-facing statement (facts only)  
- Next checkpoint time  

---

## 8. Testing & improvement

| Exercise | Cadence | Evidence |
|----------|---------|----------|
| App rollback promote | Quarterly or after major release | Time-to-restore note |
| DB restore drill (non-prod preferred) | Monthly/quarterly | Pass/fail + duration |
| Tabletop SEV1 | Quarterly | Updated Risk Register |
| DNS doc accuracy | After any DNS change | Diff vs live |

---

## 9. What this plan does **not** claim

- No multi-region active-active architecture as a guaranteed capability.  
- No contractual customer uptime SLA unless separately signed.  
- No ISO/SOC2 certified continuity program.  
- No guarantee that generated media assets are permanently archived beyond provider retention.

**Owner:** Ops Owner · **Review:** Quarterly · **Phase 11 Sprint 6**
