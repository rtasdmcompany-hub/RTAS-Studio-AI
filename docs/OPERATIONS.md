# Operations — RTAS Studio AI

Day-2 runbook: monitoring, maintenance, on-call habits.

---

## Daily / continuous

| Check | How |
|-------|-----|
| App up | Uptime monitor → `GET /api/health` |
| Ready for traffic | `GET /api/ready` (alert on 503) |
| Vercel | Failed deployments / runtime errors |
| Paddle | Webhook failure rate |
| Resend | Bounce/complaint spikes |
| fal.ai | Balance / error rate |
| GPU worker | `GET {FASTAPI_URL}/api/health` |

---

## Weekly

- Review Vercel bandwidth/function errors.
- Confirm Supabase backup job succeeded.
- `npm audit` on lockfile (schedule upgrade PRs).
- Spot-check Google OAuth login + email verification on production.

---

## Monthly

- Rotate `RTAS_ADMIN_SECRET` if shared among operators.
- Review owner/admin access list (`NEXT_PUBLIC_OWNER_EMAILS` is not authz).
- Test restore drill (staging) per [BACKUP.md](./BACKUP.md).
- Review rate-limit adequacy (move to Redis if multi-region).

---

## Health endpoints

| Path | Meaning | Expected |
|------|---------|----------|
| `/api/health` | Process alive | `200` `{ status: "ok" }` |
| `/api/ready` | Critical config present | `200` ready / `503` not_ready |
| `/api/auth/config` | Public runtime flags (+ optional worker probe) | `200` |
| `/api/auth/email-config` | Email delivery mode | `200` |
| `/api/payments/config` | Payment provider public config | `200` |

Worker: `{FASTAPI_URL}/api/health` and `/api/health/ping`.

---

## Logging & metrics

- Structured helpers: `apps/web/src/lib/observability.ts` (`logEvent`, `captureException`, `withTiming`, `trackEvent`).
- Today: console JSON-style lines on Vercel logs.
- When ready: set `NEXT_PUBLIC_SENTRY_DSN` and wire `@sentry/nextjs` into `captureException`.
- Analytics placeholders: `NEXT_PUBLIC_ANALYTICS_ID`, `NEXT_PUBLIC_POSTHOG_*`.

---

## Maintenance windows

1. Announce window.
2. Snapshot DB ([BACKUP.md](./BACKUP.md)).
3. Deploy during low traffic.
4. Run smoke from [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md).
5. Monitor `/api/ready` for 30–60 minutes.

---

## Dependency ownership

| System | Ops owner task |
|--------|----------------|
| Vercel | Domains, env, deploys |
| GitHub | Branch protection, CI |
| Supabase | DB, backups, keys |
| Resend | Domain DNS, API keys |
| Paddle | Products, webhooks, tax |
| fal.ai | Credits, API keys |
| GPU host | Uptime, CUDA, CORS, TLS |

---

## Useful commands

```bash
npm run lint -w @rtas/web
npm run typecheck -w @rtas/web
npm run test -w @rtas/web
npm run verify:production -w @rtas/web
npm run probe:services -w @rtas/web
npm run build -w @rtas/web
npm run verify:deployment-ready -w @rtas/web
```

---

## Escalation

1. Check health/ready + Vercel logs.
2. [RECOVERY.md](./RECOVERY.md) rollback.
3. Provider status pages (Vercel, Supabase, Paddle, Resend, fal).
4. Security incidents → [SECURITY.md](./SECURITY.md).
