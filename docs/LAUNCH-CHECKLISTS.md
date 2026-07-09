# Launch & operations checklists — RTAS Studio AI

Use with [DEPLOYMENT.md](./DEPLOYMENT.md), [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md), [ENVIRONMENT.md](./ENVIRONMENT.md).

---

## A. Final deployment checklist

- [ ] CI green on release commit
- [ ] `verify:deployment-ready` pass
- [ ] Vercel project = **rtas-studio-ai-web** only
- [ ] Env vars pasted from `.env.production.example` (Production)
- [ ] KV linked
- [ ] `db:push` / migrate applied
- [ ] Production deploy READY
- [ ] `/api/health` = 200
- [ ] `/api/ready` = 200 (after credentials)

---

## B. Production checklist

- [ ] `NEXTAUTH_SECRET` strong + unique
- [ ] `NEXTAUTH_URL` / `NEXT_PUBLIC_APP_URL` = HTTPS canonical
- [ ] `DATABASE_URL` pooled + TLS
- [ ] `FASTAPI_URL` public HTTPS (not localhost)
- [ ] `FAL_KEY` + credits
- [ ] Resend verified domain + `EMAIL_FROM`
- [ ] Paddle webhook secret + checkout URLs
- [ ] Google OAuth production redirect/origin
- [ ] `RTAS_ADMIN_SECRET` set
- [ ] CSP Report-Only reviewed (then enforce)

---

## C. Launch checklist

- [ ] Marketing home + pricing accurate
- [ ] Register → verify email → login
- [ ] Google login
- [ ] Dashboard `/profile`
- [ ] Studio generate (or clear simulation messaging)
- [ ] Checkout + webhook delivery
- [ ] Share link publish (same-origin media only)
- [ ] Uptime monitor on `/api/health`
- [ ] Alert on `/api/ready` 503

---

## D. Rollback checklist

- [ ] Note last good Vercel deployment ID before release
- [ ] Promote previous READY deployment
- [ ] If env caused outage: fix env → Redeploy
- [ ] If schema caused outage: restore DB ([BACKUP.md](./BACKUP.md)) then promote app
- [ ] Re-smoke `/api/health` + login
- [ ] Details: [RECOVERY.md](./RECOVERY.md)

---

## E. Disaster recovery checklist

- [ ] DB backup restore tested in staging
- [ ] Password vault has all production secrets
- [ ] GPU worker restart procedure documented
- [ ] Paddle webhook replay procedure known
- [ ] Resend domain/DNS recovery known
- [ ] Comms template ready ([RECOVERY.md](./RECOVERY.md))

---

## F. Environment variable checklist

Required for commercial go-live (see [ENVIRONMENT.md](./ENVIRONMENT.md)):

| Variable | Status |
|----------|--------|
| `NEXTAUTH_SECRET` | ☐ |
| `NEXTAUTH_URL` | ☐ |
| `NEXT_PUBLIC_APP_URL` | ☐ |
| `DATABASE_URL` | ☐ |
| `FASTAPI_URL` | ☐ |
| `KV_REST_API_URL` + `KV_REST_API_TOKEN` | ☐ |
| `FAL_KEY` | ☐ |
| `RESEND_API_KEY` + `EMAIL_FROM` | ☐ |
| `PADDLE_WEBHOOK_SECRET` + checkout URLs | ☐ |
| Google OAuth pair (if enabled) | ☐ |
| `RTAS_ADMIN_SECRET` | ☐ |
| `NEXT_PUBLIC_OWNER_EMAILS` (ops UI) | ☐ |

Placeholders only until accounts exist — app fails closed / warns; no hardcoded secrets.

---

## G. DNS checklist

- [ ] Apex + www → Vercel
- [ ] SSL issued
- [ ] `api.` → GPU host (when ready)
- [ ] Resend SPF/DKIM/DMARC
- [ ] OAuth origins updated
- [ ] Webhook URLs updated
- [ ] See [INFRASTRUCTURE.md](./INFRASTRUCTURE.md)

---

## H. Monitoring checklist

- [ ] Uptime: `GET /api/health`
- [ ] Readiness: `GET /api/ready` (public minimal; details with admin secret)
- [ ] Vercel runtime logs
- [ ] Paddle webhook failure alerts
- [ ] Resend bounce/complaint watch
- [ ] fal.ai balance watch
- [ ] Optional: `NEXT_PUBLIC_SENTRY_DSN` when Sentry account ready
