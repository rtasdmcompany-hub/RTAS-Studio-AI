# Release Candidate maintenance — RC1

**Status:** Release Candidate 1 (RC1)  
**Baseline commit:** `3bd9a02` (productization) on `master`  
**Live project:** `rtas-studio-ai-web` → https://rtas-studio-ai-web.vercel.app

Engineering and productization are **frozen** except for maintenance.

---

## Scope (allowed)

| Allowed | Not allowed |
|---------|-------------|
| Fix confirmed production/regression bugs | Redesign or UX experiments |
| Documentation corrections | New features |
| CI/CD health fixes | Refactors “for cleanliness” |
| Safe patch dependency updates | Major version upgrades without need |
| Deployment script / env template accuracy | Changing credentials or inventing secrets |
| Monitoring / probe script fixes | Breaking API or auth contracts |

Major product changes wait for **beta user feedback**.

---

## Health checks (run periodically)

```bash
# Live
curl -sS https://rtas-studio-ai-web.vercel.app/api/health

# Local quality (CI-equivalent)
npm run lint -w @rtas/web
npm run typecheck -w @rtas/web
npm run test -w @rtas/web
npm run verify:deployment-ready -w @rtas/web
npm run build -w @rtas/web
```

See [RC1-STATUS-REPORT.md](./RC1-STATUS-REPORT.md) for the latest gate matrix.

---

## Dependency policy

1. Prefer **patch** updates within existing major ranges.
2. Do not bump Next.js major without an explicit upgrade project.
3. After any lockfile change: lint, typecheck, smoke, build must pass.
4. Never commit `.env.local` or secrets.

---

## Deploy policy

- Only deploy **rtas-studio-ai-web**.
- Prefer Git push to `master` (Vercel Git integration).
- If GitHub commit status shows a failed **Vercel - rtas-studio-ai** check, disconnect that stale project from the repo (RC1 target is `rtas-studio-ai-web` only).
- Rollback: promote previous READY deployment in Vercel ([RECOVERY.md](./RECOVERY.md)).

---

## Change control

1. Reproduce bug or document CI failure.
2. Minimal fix + test.
3. Update release notes if user-visible.
4. Push; confirm Vercel READY + `/api/health`.

---

## Related

- [PRODUCT-READINESS-REPORT.md](./PRODUCT-READINESS-REPORT.md)
- [RELEASE-REPORT.md](./RELEASE-REPORT.md)
- [RELEASE-NOTES.md](./RELEASE-NOTES.md)
- [OPERATIONS.md](./OPERATIONS.md)
