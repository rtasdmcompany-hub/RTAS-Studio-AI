# RTAS Studio AI — Final Enterprise Audit Report

**Date:** 19 July 2026  
**Mode:** Independent production review (no new features; UI fixes limited to defects)  
**Scope:** Monorepo `apps/web`, `apps/backend`, `packages/*`, docs, deploy config

---

## Executive verdict

RTAS Studio AI is a large Phase 1–10 enterprise SaaS codebase with strong **commercial web gateways** (NextAuth, rate limits, magic-byte uploads, webhook HMAC + idempotency) and a mature **engine catalog** (billing, marketplace, observability, DR, RC-2).

It is **not** yet at Google/Stripe-grade production hardness on the FastAPI worker boundary. Several trust-boundary gaps remained after Phase 10 and were **fixed in this audit**; residual risks are documented below.

**Overall production readiness (post-fix fixes): ~86%**

---

## Scores (0–100)

| Area | Score | Notes |
|------|------:|-------|
| Overall Architecture | 82 | Clear monorepo; too many in-memory “engines” vs durable web path |
| Frontend | 84 | Strong studio/marketing; dark-only; a11y gaps addressed |
| Backend | 80 | Rich FastAPI surface; worker auth now tightened |
| Database | 86 | Prisma + pooler docs; optional `directUrl` still thin |
| Security | 88 | Critical generate/callback/media holes closed this pass |
| Performance | 78 | Web optimized; backend orchestration not horizontally scaled |
| AI Engine | 83 | Failover + Fal path solid; RunPod live still deferred |
| Marketplace | 80 | Feature complete; many stores in-memory |
| Billing | 87 | MoR + web idempotency; backend unsigned only if misconfigured historically |
| Developer Platform | 76 | APIs exist; signing now env-backed |
| Documentation | 85 | ENVIRONMENT/DEPLOYMENT/SECURITY present |
| Code Quality | 74 | Huge surface; duplicate auth helpers remain |
| **Production Readiness %** | **86** | Ready for controlled launch with ops checklist |

---

## Issues found & disposition

### CRITICAL (fixed this audit)

| ID | Issue | Fix |
|----|--------|-----|
| C1 | Unauthenticated `/api/generate` (+ `/async`) — Fal spend + secret callback exfil | `Depends(require_backend_secret)` on both handlers |
| C2 | Pipeline callbacks sent `AI_BACKEND_SECRET` to any URL | `assert_safe_callback_url` allowlist + no redirects |
| C3 | Public `/media/outputs` in production | Mount disabled in production (with uploads) |

### HIGH (fixed this audit)

| ID | Issue | Fix |
|----|--------|-----|
| H1 | Admin Fal reset fail-open when secret unset | Fail-closed via `require_backend_secret` |
| H2 | Jobs routes used local fail-open auth | Delegates to centralized fail-closed helper |
| H3 | Legacy provider job status/cancel unauthenticated | Requires backend secret |
| H4 | Hardcoded HASH/SIGNING secrets | Env-backed `signing_secrets.py` (prod refuses defaults) |
| H5 | `sign_body` fell back to `rtas-dev-only-jwt` in prod | Removed fallback |
| H6 | SSRF: redirects after allowlist; fal_multiclip ungarded | `follow_redirects=False` + clip URL guard |

### HIGH / MEDIUM (documented — remaining)

| ID | Issue | Status |
|----|--------|--------|
| R1 | Dozens of routes still use local `_auth` that fail-open if secret unset | **Partial** — migrate remaining to `require_backend_secret` |
| R2 | Job orchestration / many Phase 7–9 stores are in-memory (not multi-replica HA) | **Documented** — durable path is Prisma `GenerationJob` |
| R3 | Webhook claim file store not fully atomic under concurrent retries | **Documented** — prefer Redis/Prisma claim |
| R4 | Dark-only theme (no light/system) | **Documented** — intentional brand; `color-scheme: dark` |
| R5 | Backend unsuitable on Vercel Python for long GPU workers | **Documented** — keep long-lived FastAPI |
| R6 | Full live GPU E2E not re-run in this audit | **Ops** — use RC-2 + staging Fal job |
| R7 | Remaining duplicate fail-open auth across marketplace/billing family | **Backlog** |

### UI / UX (fixed this audit)

| ID | Issue | Fix |
|----|--------|-----|
| U1 | Missing `global-error.tsx` | Added |
| U2 | Hero category grid stuck at 5 columns on mobile | Responsive 3→2→1 columns |
| U3 | Account menu unlabeled when name CSS-hidden | `aria-label` on trigger |
| U4 | Live chat `aria-controls` missing target id | `id="rtas-live-chat-panel"` |
| U5 | Gallery Delete only on failed items | Delete for completed assets |

---

## Stage summaries

### 1 — Source code
- No committed `.env` secrets (examples only).
- Debug `print`/`console.log` sweeps were clean in targeted scans.
- Large codebase with many parallel engines; dead-code removal deferred where engines are Phase-registered.

### 2 — Architecture
- Correct pattern: Next.js = commercial edge; FastAPI = GPU worker.
- Weakness: treating FastAPI as semi-public historically; trust boundary now enforced harder.
- Queue HA is simulation-grade on backend; production jobs should stay on Prisma.

### 3 — UI/UX
- Error/404/empty/loading mostly present.
- Defects above fixed; no brand redesign.

### 4 — Performance
- GZip, indexes, job caps from Phase 10 Sprint 2 remain.
- Bundle/lazy-loading: acceptable for Next 14; Next 15 upgrade still recommended as hygiene.

### 5 — Security (OWASP-oriented)
- AuthN/AuthZ on worker generate now required.
- SSRF and media exposure tightened.
- Residual: migrate all `_require_*` helpers to central auth.

### 6 — E2E
- Automated RC-2 module validation (Sprint 9) = 100% package/route presence.
- Live signup→render→pay not executed in this pass (requires secrets + Fal balance).

### 7 — Production validation
- Prod `/api/ready` previously stamped Sprint 9 / RC-2.
- Redeploy API after this audit for security fixes to go live.

### 8 — External bar (Google / Stripe / Vercel style)
- **Would block launch on:** unauthenticated generate + secret callbacks (now fixed).
- **Would warn on:** in-memory enterprise engines, incomplete auth migration, dark-only a11y theme preference.
- **Would accept:** MoR billing, NextAuth gateways, webhook idempotency, DR/observability packages.

---

## Launch blockers remaining (ops, not code)

1. Confirm `AI_BACKEND_SECRET` set on **both** Vercel web + API.  
2. `prisma migrate deploy` on production DB.  
3. Staging Fal generation smoke.  
4. Migrate remaining fail-open route helpers (R1).  
5. Optional: rotate signing secrets into dedicated env keys (`RTAS_*_SIGNING_SECRET`).

---

## Changes shipped in this audit

Backend: generate auth, admin fail-closed, jobs auth, callback SSRF, media mounts, signing secrets, storage/fal SSRF, JWT sign_body.  
Web: `global-error`, hero responsive, account aria-label, live-chat id, gallery delete.
