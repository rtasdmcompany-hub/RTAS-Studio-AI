# Vercel Build Root-Cause Report

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Date:** 24 July 2026  
**Phase:** 13 — CTO Build Failure Root-Cause Investigation  

---

## Verdict

Production deployment is **READY**.

| Item | Value |
|------|--------|
| Successful deploy | `dpl_7cspZ9anUg9dDsDGfukCAxuWHgTn` |
| Commit | `4dd6713` — `fix(build): Suspense-wrap PromotionAttributionTracker for static prerender` |
| Production URL | https://rtasstudio.com (aliased from Vercel production) |
| Prior failed deploys | `dpl_FPRUP4QHuBXk5VK1PwYNBSFmPUfP`, `dpl_DvxytUVTTwNrTb52eorTf2BgxbAP` (ERROR — superseded) |

---

## Investigation method

1. Listed latest production deployments via Vercel API (`apps/web/scripts/check-vercel-deploy.mjs`).
2. Fetched **complete** build event logs for the latest ERROR deploy.
3. Identified the **first** hard stop error only (ignored cascades).
4. Fixed that cause, pushed, re-read the next failure if any.
5. Repeated until Production reached READY.

No speculative rewrites. No disabling TypeScript/ESLint. No business-logic changes beyond type/Suspense correctness required for build.

---

## Root cause chain (two sequential first errors)

Vercel failed twice for **different first errors**. Both were real; both had to be fixed in order.

### Failure A — TypeScript compile error

| Field | Detail |
|-------|--------|
| **Category** | TypeScript compile error (Next.js “Linting and checking validity of types”) |
| **Deploy** | `dpl_FPRUP4QHuBXk5VK1PwYNBSFmPUfP` |
| **Commit** | `0112368` |
| **First error** | `apps/web/src/lib/promotions/engine.ts` — `audienceOverrides: PromotionAudienceRules \| null` assigned where `PromotionVariant` expects `PromotionAudienceRules \| undefined` |

Webpack had already printed **Compiled successfully**. The build stopped in the typecheck phase.

**Why:** Revenue Promotion Engine mapped Prisma/`safeAudienceRules()` (`null`) onto an optional TS field (`undefined` only). Strict null checks reject that.

**Fix commits:** `4cf165e`, `97f9f3d` (engine + remaining typecheck blockers surfaced by local `tsc`).

### Failure B — Next.js static generation / Client Component

| Field | Detail |
|-------|--------|
| **Category** | Client Component error / Route generation error (static prerender) |
| **Deploy** | `dpl_DvxytUVTTwNrTb52eorTf2BgxbAP` |
| **Commit** | `97f9f3d` (typecheck green; prerender failed) |
| **First error** | `useSearchParams() should be wrapped in a suspense boundary at page "/auth/check-email"` |

Cascades to homepage, studio, admin, and many other routes were **downstream** of the same root mount — not separate bugs.

**Why:** `PromotionAttributionTracker` calls `useSearchParams()` and was mounted in root `AppProviders` **without** `<Suspense>`. Next.js requires a Suspense boundary for that hook during static prerender. Auth pages already Suspense-wrapped their own clients; the global tracker was the missing boundary.

**Fix commit:** `4dd6713` — wrap tracker in `<Suspense fallback={null}>` inside `AppProviders.tsx`.

---

## Files changed (build-failure repairs only)

| File | Change |
|------|--------|
| `apps/web/src/lib/promotions/engine.ts` | Do not assign `null` to `audienceOverrides`; Prisma JSON via `Prisma.JsonNull` / `InputJsonValue` |
| `packages/shared/src/legal/privacy.ts` | Import missing `LEGAL_JURISDICTION` |
| `packages/utils/src/payments/registry.ts` | Narrow recommended provider away from `"manual"` before indexing adapters |
| `packages/utils/src/payments/process-event.ts` | Fix `ignored` webhook branch narrowing |
| `apps/web/src/components/providers/AppProviders.tsx` | Suspense-wrap `PromotionAttributionTracker` |
| `docs/business/VERCEL_BUILD_ROOT_CAUSE_REPORT.md` | This report |

---

## Commands executed

| Command | Result |
|---------|--------|
| Vercel API: list production deployments | Confirmed ERROR → BUILDING → READY |
| Vercel events log for failed deploys | Captured first errors for Failure A and B |
| `npm run lint` (`apps/web`) | **PASS** (exit 0; react-hooks warnings only) |
| `NODE_OPTIONS=--max-old-space-size=8192 npm run typecheck` | **PASS** (exit 0) after TS fixes |
| `npm run build` (local) | Webpack **Compiled successfully**; workstation stalled >90m on Next embedded typecheck after lint — killed. Authoritative gates: local `typecheck` PASS + Vercel production build **READY** |
| `git commit` / `git push origin HEAD` | Pushed through `4dd6713` |

---

## Local build status

| Gate | Status |
|------|--------|
| Lint | **PASS** |
| Typecheck | **PASS** |
| Full local `next build` wall-clock completion | **INCONCLUSIVE on this workstation** (resource hang after successful compile; not a remaining type/prerender error — Vercel completed the same pipeline to READY) |

---

## Production deployment status

| Item | Status |
|------|--------|
| Latest production deploy | **READY** — `dpl_7cspZ9anUg9dDsDGfukCAxuWHgTn` |
| Commit on READY deploy | `4dd6713` |
| Failed deploys after READY | None (latest is READY) |

---

## Remaining issues (non-blocking for this investigation)

1. Local full `next build` remains slow/hang-prone on this machine during Next’s embedded typecheck; use `npm run typecheck` + Vercel as CI truth until workstation resources improve.
2. Unrelated dirty working-tree files were **not** included in these fix commits.
3. Commercial blockers outside build scope (Paddle purchase→credits E2E, live Fal generation, pending Prisma migrations on prod if any) are **not** caused by this build failure chain.

---

## Summary

| # | Category | First error location | Fix |
|---|----------|----------------------|-----|
| 1 | TypeScript compile error | `promotions/engine.ts` null vs undefined | `4cf165e` / `97f9f3d` |
| 2 | Client Component / route prerender | Global `useSearchParams` without Suspense | `4dd6713` |

**Production is GREEN.**
