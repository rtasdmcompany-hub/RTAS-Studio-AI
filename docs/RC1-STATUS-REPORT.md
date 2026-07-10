# RC1 Status Report — RTAS Studio AI

**Date:** 2026-07-10  
**Owner:** Release Candidate (RC1)  
**Scope:** Code-related release gates only (external MoR/domain/GPU credentials deferred)

---

## Gate results

| Check | Result | Notes |
|-------|--------|-------|
| GitHub Actions (`CI - RTAS Web`) | **PENDING → verify after push** | Prior failure root cause fixed (see below) |
| TypeScript | **PASS** | `prisma generate && tsc --noEmit` |
| ESLint | **PASS** | Warnings only (a11y/hooks); exit 0 |
| Production Build | **PASS** (local) | `prisma generate && next build` |
| Vercel Deploy | **PENDING → verify after push** | Git integration on `master` → `rtas-studio-ai-web` |
| Smoke Tests | **PASS** | 10/10 commercial smoke |

External (ignored for RC1 code gate): Paddle webhook, custom domain, Resend production domain, public GPU `FASTAPI_URL`.

---

## Prior CI failure (fixed)

Latest failed run: https://github.com/rtasdmcompany-hub/RTAS-Studio-AI/actions/runs/29087688395  
(`8ac6a5e`, TypeScript step, exit 2)

Annotations:
1. `Module '"@prisma/client"' has no exported member 'User'.`
2. Cascading `Parameter 'row' implicitly has an 'any' type.`

**Cause:** CI ran `tsc` without generating the Prisma client. Local machines already had a generated client, so typecheck passed locally but failed on clean CI runners.

**Fix:**
- `apps/web` `typecheck` script now runs `prisma generate && tsc --noEmit`
- `ci-web.yml` adds an explicit **Generate Prisma client** step before TypeScript
- Job-level `DATABASE_URL` placeholder for Prisma tooling
- Manual `deploy-web.yml` no longer hard-fails when Vercel secrets are missing (skips cleanly; primary CD remains Vercel Git Integration)
- Branch protection docs updated to required check name: `Lint · Typecheck · Smoke · Ready · Build`

---

## Local verification commands (CI-equivalent)

```bash
npm install --workspace=@rtas/web --include-workspace-root --legacy-peer-deps --no-audit --no-fund
# with RTAS_ALLOW_INCOMPLETE_ENV=1 and CI placeholder env vars:
npm run verify:deployment-ready -w @rtas/web
npm run lint -w @rtas/web
npm run typecheck -w @rtas/web
npm run test -w @rtas/web
npm run verify:production -w @rtas/web
npm run build -w @rtas/web
```

---

## Related

- [RC1-MAINTENANCE.md](./RC1-MAINTENANCE.md)
- [GITHUB-BRANCH-PROTECTION.md](./GITHUB-BRANCH-PROTECTION.md)
- [developer/TROUBLESHOOTING.md](./developer/TROUBLESHOOTING.md)
- [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md)
