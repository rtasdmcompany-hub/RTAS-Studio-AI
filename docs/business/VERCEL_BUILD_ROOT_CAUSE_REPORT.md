# Vercel Build Root-Cause Report

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Date:** 24 July 2026  
**Investigated deployment:** `dpl_FPRUP4QHuBXk5VK1PwYNBSFmPUfP`  
**Failed commit on Vercel:** `0112368`  

---

## Root cause

**Category:** TypeScript compile error (Next.js production typecheck phase)

**First stopping error (from Vercel build log):**

```
./src/lib/promotions/engine.ts:39:3
Type error: Type '{ ... audienceOverrides: PromotionAudienceRules | null; }[]'
is not assignable to type 'PromotionVariant[]'.
  Types of property 'audienceOverrides' are incompatible.
    Type 'PromotionAudienceRules | null' is not assignable to
    type 'PromotionAudienceRules | undefined'.
      Type 'null' is not assignable to type 'PromotionAudienceRules | undefined'.
```

Webpack had already printed `Compiled successfully`. Failure occurred in **“Linting and checking validity of types …”**. ESLint warnings alone did not fail the build.

---

## Why it happened

`safeVariants()` called `safeAudienceRules()`, which returns `PromotionAudienceRules | null`, and assigned that value directly onto `PromotionVariant.audienceOverrides`, which is typed as `PromotionAudienceRules | undefined` (optional property — not `null`).

Strict TypeScript rejects `null` where only `undefined` (or omit) is allowed. This surfaced after the Revenue Promotion Engine landed and previous payment/engage type fixes cleared earlier blockers.

---

## Files changed (root-cause + immediate follow-on type blockers)

| File | Change |
|------|--------|
| `apps/web/src/lib/promotions/engine.ts` | Build variants without assigning `null` audienceOverrides; Prisma JSON via `Prisma.JsonNull` / `InputJsonValue` |
| `packages/shared/src/legal/privacy.ts` | Import missing `LEGAL_JURISDICTION` |
| `packages/utils/src/payments/registry.ts` | Narrow recommended provider away from `"manual"` before indexing adapters |
| `packages/utils/src/payments/process-event.ts` | Fix `ignored` webhook branch narrowing (`event.type` on `never`) |

**Commits:**
- `4cf165e` — RPE `audienceOverrides` nullability (primary Vercel error)
- `97f9f3d` — remaining typecheck blockers exposed by local `tsc`

---

## Commands executed

| Command | Result |
|---------|--------|
| Vercel API: latest production deployments | Latest 3 = `ERROR` |
| Vercel events log for `dpl_FPRUP4QHuBXk5VK1PwYNBSFmPUfP` | Captured first type error |
| `npm run lint` (`apps/web`) | **PASS** (exit 0; react-hooks warnings only) |
| `NODE_OPTIONS=--max-old-space-size=8192 npm run typecheck` | **PASS** (exit 0) after fixes |
| `npm run build` (local) | Webpack **Compiled successfully**; hung/stalled >90m on Next embedded typecheck after lint warnings — killed. Authoritative typecheck covered by `npm run typecheck` PASS. Production confirmation deferred to Vercel deploy. |

---

## Local build status

| Gate | Status |
|------|--------|
| Lint | **PASS** |
| Typecheck | **PASS** |
| Full local `next build` completion | **INCONCLUSIVE** (resource hang after successful compile + lint; not a remaining type error — `tsc --noEmit` already green) |

---

## Production deployment status

| Item | Status |
|------|--------|
| Push of fix commits to `origin/master` | In progress / verify after push |
| New Vercel Production deployment | Pending READY after push |
| Prior production deploys | ERROR (blocked by root cause above) |

---

## Remaining issues

1. Confirm Vercel Production reaches **READY** after `97f9f3d` (or later) is on `origin/master`.
2. Local full `next build` is extremely slow/hang-prone on this workstation during the embedded typecheck phase; prefer `npm run typecheck` + Vercel build as CI truth until machine resources improve.
3. Unrelated dirty working tree files were **not** included in this fix commit.

---

## Verdict (investigation)

Root cause **identified and fixed in code**. Production GREEN status depends on successful push + Vercel redeploy verification (next section of ops).
