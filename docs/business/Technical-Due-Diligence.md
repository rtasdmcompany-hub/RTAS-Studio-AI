# RTAS Studio AI — Technical Due Diligence

**Classification:** Confidential — Technical / M&A diligence  
**Product:** RTAS Studio AI v1.0 · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (Pakistan)  
**Phase:** 11 · Sprint 3  
**Stack (verified):** Next.js · FastAPI · Prisma/Supabase · Fal.ai · Resend · Vercel · Cloudflare · Paddle (MoR)

**Cross-links:** `docs/ARCHITECTURE.md` · `docs/SECURITY.md` · `docs/ACTIVE-STACK.md` · `docs/KNOWN_LIMITATIONS.md` · `docs/INFRASTRUCTURE.md` · `/business/company/COMPANY_OVERVIEW.md`

---

## 1. Executive technical verdict

RTAS Studio AI is a **coherent, production-shaped SaaS system**: authenticated Studio UX, credit-metered generation, job orchestration against licensed model APIs, MoR webhook entitlement design, and a documented security baseline. Diligence risk concentrates in **external dependencies** (Paddle live checkout, Fal wallet, single-operator ops), **early monitoring/DR maturity**, and **honest absence of exclusive foundation-model IP**—not in “demo-only” frontend theater.

---

## 2. Architecture overview

```
Web (Next.js on Vercel)
  Auth · Studio · Profile · Admin · Marketing · SEO
        │
        ├─ BFF API routes (session, admin, webhooks, checkout)
        ├─ Prisma → Supabase Postgres (pooled)
        ├─ Redis/KV / in-memory helpers (rate limits)
        ├─ Resend (transactional email)
        └─ Paddle (MoR checkout + webhooks → credits)
                │
                ▼
        FastAPI GPU worker (FASTAPI_URL)
                │
                ▼
        Fal.ai tier routing (Economy / Enterprise cost paths)
```

**Ownership boundary (critical for buyers):** RTAS owns UX, billing/credits, watermark/policy posture, category workflows, and orchestration. RTAS **does not** own proprietary foundation-model weights; generation uses **licensed APIs**.

---

## 3. Application surfaces

| Surface | Role | Diligence notes |
|---------|------|-----------------|
| Marketing site | Acquisition & trust | Legal pages v1.1; AUP-safe Identity Preservation messaging |
| Auth | Credentials + Google OAuth | Email verification required for credentials; OAuth linking hardened |
| Studio | Prompt/image → video | Credit checks, progress/ETA, category validation |
| Profile / library | Assets & entitlements | Download gated by subscription entitlement |
| Admin | Ops metrics | Secret-gated; MRR estimate not Paddle-ledger reconciled |
| Help / feedback | Support | Live help center surfaces |

---

## 4. Data & persistence

| Store | Use | Risk / control |
|-------|-----|----------------|
| Supabase Postgres via Prisma | Users, jobs, credits, logs | Prefer TLS/`sslmode=require`; pooled URL for serverless |
| Object/video URLs from providers | Generated outputs | Dependency on provider URL lifetime & storage policy |
| Session JWT (NextAuth) | AuthN | Stateless sessions; “logout all devices” needs future sessionVersion |
| Ephemeral rate-limit stores | Abuse control | In-memory may not share across multi-instance without KV |

**Personal data:** Account email, profile, generation metadata, support communications — governed by Privacy Policy. Buyer must plan transfer / controller change notices if acquiring.

---

## 5. Generation pipeline (technical flow)

1. User selects mode (prompt | image), category, visual style.  
2. Shared package validates category fields.  
3. Server-side credit check and generation guard.  
4. `GenerationJob` lifecycle: QUEUED → … → COMPLETED / FAILED.  
5. Fal model selection by billing-tier cost routing.  
6. Studio polls progress / ETA.  
7. Output URL returned; entitlement gates download.

**Credit math:** 1 credit = 1 second of finished video (product rule). Tester / Standard / Premium quotas live in shared catalog + backend.

**Long-form behavior (product truth):** Standard/Premium long requests may split into segments with stitch behavior per product rules; Tester duration capped.

---

## 6. Billing & entitlements (engineering view)

| Component | Status |
|-----------|--------|
| Price tiers in shared packages | Complete |
| Checkout API routes | Complete |
| Paddle webhook HMAC verify, fail-closed | Complete (design) |
| Credit grant on subscription activation | Complete |
| Live MoR checkout enabled on seller account | **Business/ops gap — may still be pending** |
| Admin MRR vs Paddle ledger reconciliation | Partial (estimate only) |

Technical diligence should **separate code readiness from merchant-account readiness**.

---

## 7. Security posture

### Strengths
- Secrets not intended for git; production fail-closed for missing payment secrets.  
- Webhook signature verification.  
- Security headers (HSTS, frame deny, nosniff, referrer, permissions policy).  
- Admin APIs require `RTAS_ADMIN_SECRET`.  
- Password reset: HMAC token, short TTL, rate limited.  
- Documented pre-launch / enterprise security audit materials in `docs/`.

### Gaps / accepted limitations
- CSP Report-Only (enforcing mode deferred).  
- No SOC 2 / ISO claim.  
- No third-party penetration test evidenced in-repo.  
- Rate limiting may need Redis/KV for horizontal scale.  
- Admin UI secret-gated in-browser (APIs stricter).

---

## 8. Infrastructure & deployment

| Layer | Provider | Notes |
|-------|----------|-------|
| Web hosting | Vercel | Primary production |
| DNS / edge | Cloudflare (+ Vercel DNS history) | Domain docs exist |
| Database | Supabase | Postgres + pooler |
| Email | Resend | Verification / reset |
| MoR | Paddle | Tax/invoicing intent |
| Inference | Fal.ai | Wallet balance is runtime dependency |
| OAuth | Google | Console redirect allowlist discipline required |

**Deploy diligence artifacts:** `docs/DEPLOYMENT.md`, `docs/VERCEL-DEPLOY.md`, `docs/PRODUCTION.md`, `docs/ENVIRONMENT.md`.

---

## 9. Scalability considerations

| Dimension | Current posture | Buyer implication |
|-----------|-----------------|-------------------|
| Web tier | Serverless horizontal | Scales with Vercel; watch cold starts & DB pool |
| Job throughput | Worker + Fal concurrency | Bound by Fal limits & wallet |
| Database | Managed Postgres | Indexing & job caps noted in enterprise audits |
| Multi-region | Not active-active | Acceptable for early stage; enterprise may demand plan |
| Cost scaling | Inference-heavy COGS | Gross margin diligence mandatory |

---

## 10. Reliability, monitoring, DR

| Area | Assessment |
|------|------------|
| Backup/recovery documentation | Present |
| Proven restore drills | Limited evidence — treat as Partial |
| Status page | Partially static messaging |
| Admin aggregates | Useful early ops signal |
| Formal SLOs / paging | Immature |
| Dependency outage playbooks | Knowledge exists; formalize in BCP |

---

## 11. Codebase & engineering quality signals

| Signal | Observation |
|--------|-------------|
| Monorepo structure | `apps/web`, `apps/backend`, `packages/shared` — clear boundaries |
| Shared credit/pricing source of truth | Reduces drift risk |
| Legal modules in shared package | Supports consistent trust copy |
| Documentation density | High relative to stage |
| Test maturity | Smoke/gates documented; full coverage % not packaged for DD |
| Known limitations disclosure | Strong honesty signal for buyers |

---

## 12. Intellectual property & third-party tech

| Asset | Owned by RTAS? | Diligence action |
|-------|----------------|------------------|
| Application source & UX | Yes (assert via assignments) | Confirm contractor/employee IP |
| Category schemas / workflows | Yes | |
| Brand & domain | Operator-controlled | Transfer mechanics |
| Fal models / weights | No | Contract assignment / continued access |
| Paddle / Vercel / Supabase / Resend | Licensed services | Account transfer plan |
| Open-source dependencies | Mixed licenses | SBOM + NOTICE |

---

## 13. Compliance-relevant technical controls

- Product marketing and Studio notices aligned to **Identity Preservation** (authorized use), not deepfake/face-swap promotion.  
- Trust & Safety / AI Policy routes live.  
- Prohibited-use language expanded for MoR AUP alignment.  
- Buyer should verify ongoing content-moderation ops capacity as volume grows.

---

## 14. Integration map (systems of record)

| System | SoR for |
|--------|---------|
| Supabase/Prisma | Accounts, jobs, credits ledger (app) |
| Paddle | Payments, tax invoices (when live) |
| Fal | Model inference execution |
| Resend | Transactional email delivery |
| Vercel | Web deployment & env |
| Cloudflare | DNS / edge controls |
| Google | OAuth identity provider |

---

## 15. Known risks (technical)

| Risk | Severity | Notes |
|------|----------|-------|
| Paddle checkout not live | High (commercial) | Blocks revenue proof |
| Fal balance / provider outage | High | Generation halt |
| Key-person ops knowledge | High | Access & runbooks |
| Stateless session logout-all | Medium | Product limitation |
| CSP not enforcing | Medium | XSS defense-in-depth gap |
| Rate limit store not distributed | Medium | Abuse under scale |
| Provider URL expiry for assets | Medium | Library durability |
| Admin MRR estimate drift | Low–Medium | Finance diligence noise |
| Single-region posture | Medium | Enterprise RFPs |

---

## 16. Future improvements (post-v1.0, non-binding)

1. Enforce CSP after embed QA.  
2. Redis/KV rate limits across instances.  
3. `sessionVersion` for global logout.  
4. Paddle ledger reconciliation for admin finance views.  
5. Formal OpenAPI export & broader automated tests.  
6. Documented RTO/RPO with quarterly restore drills.  
7. Optional enterprise SSO path when ICP demand proven.  
8. SBOM generation in CI for every release.  
9. Deeper live status probes on public status surface.  
10. Multi-provider inference failover design (cost vs resilience).

---

## 17. Diligence request list (technical)

Buyers typically request:

1. Read-only repo access + architecture walkthrough.  
2. Environment variable inventory (names only) + secret custody model.  
3. Last 90 days of error/uptime signals (export).  
4. Fal spend vs generations unit-economics sample.  
5. Webhook & checkout end-to-end demo on **sandbox or live**.  
6. Restore test from latest DB backup.  
7. Access matrix for all vendor consoles.  
8. Dependency license report.

---

## 18. Technical DD score (documentation & system maturity)

| Dimension | Score (0–100) |
|-----------|---------------|
| Architecture clarity | 88 |
| Production completeness (v1.0) | 86 |
| Security baseline | 74 |
| Operability / DR | 62 |
| Scalability readiness | 68 |
| IP / dependency transparency | 80 |
| **Technical DD composite** | **76** |

Interpretation: **B** technical package for an early commercial SaaS asset—stronger on build completeness than on enterprise ops certification.

---

*Companion: `Acquisition-Readiness-Checklist.md`, `Risk-Assessment.md`, `Business-Due-Diligence.md`.*
