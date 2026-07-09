# Release checklist — RTAS Studio AI

Use this checklist for every production release. External credentials may still be pending during engineering readiness; mark those items **N/A — pending account** rather than skipping the section.

---

## Pre-deployment

### Engineering

- [ ] CI green on release commit (`.github/workflows/ci-web.yml`)
- [ ] `npm run lint -w @rtas/web`
- [ ] `npm run typecheck -w @rtas/web`
- [ ] `npm run test -w @rtas/web` (commercial smoke)
- [ ] `npm run build -w @rtas/web`
- [ ] `npm run verify:deployment-ready -w @rtas/web`
- [ ] No secrets in git status (`.env.local` untracked)
- [ ] Security headers present in `vercel.json`
- [ ] Health routes present: `/api/health`, `/api/ready`

### Configuration (fill when accounts exist)

- [ ] `apps/web/.env.production.example` values prepared in vault
- [ ] `NEXTAUTH_SECRET` strong and unique
- [ ] `NEXTAUTH_URL` / `NEXT_PUBLIC_APP_URL` = HTTPS canonical domain
- [ ] `DATABASE_URL` pooled Postgres
- [ ] KV / Upstash linked
- [ ] `FASTAPI_URL` public HTTPS (not localhost)
- [ ] `FAL_KEY` (or alternate AI key) + credits
- [ ] Resend key + verified `EMAIL_FROM`
- [ ] Paddle webhook secret + checkout URLs (or Lemon equivalents)
- [ ] Google OAuth production redirect/origin (if enabled)
- [ ] `RTAS_ADMIN_SECRET` set

### Infrastructure

- [ ] DNS plan documented ([INFRASTRUCTURE.md](./INFRASTRUCTURE.md))
- [ ] Webhook URLs planned for Paddle/Lemon
- [ ] GPU host CORS includes app origin
- [ ] Backup verified or scheduled ([BACKUP.md](./BACKUP.md))

---

## Deployment

- [ ] Env vars set in Vercel (Production)
- [ ] KV linked
- [ ] Schema applied (`db:push` or migrate)
- [ ] Deploy production (Vercel)
- [ ] Custom domain + SSL active (when domain ready)
- [ ] Google OAuth console updated
- [ ] Paddle/Lemon webhook pointed at production
- [ ] Resend domain verified

---

## Post-deployment

- [ ] `GET /api/health` → 200
- [ ] `GET /api/ready` → 200
- [ ] Marketing home loads
- [ ] Register + email verification
- [ ] Login (credentials)
- [ ] Google login (if enabled)
- [ ] Dashboard `/profile` loads
- [ ] Studio opens
- [ ] Generation path (or clear simulation messaging)
- [ ] Checkout starts (test mode acceptable pre-launch)
- [ ] Webhook delivers test event
- [ ] `npm run probe:services -w @rtas/web` against prod-shaped env

---

## Smoke tests (automated + manual)

```bash
npm run test -w @rtas/web
npm run verify:production -w @rtas/web
npm run probe:services -w @rtas/web
```

Manual matrix: auth → verify → dashboard → studio → pay → webhook → generate.

---

## Rollback

- [ ] Know last good Vercel deployment ID before release
- [ ] Rollback steps reviewed ([RECOVERY.md](./RECOVERY.md))
- [ ] DB snapshot taken if schema changes

---

## Monitoring

- [ ] Uptime check on `/api/health`
- [ ] Alert on `/api/ready` = 503
- [ ] Vercel error log watch (first 1h)
- [ ] Paddle webhook log watch
- [ ] fal balance check
- [ ] Sentry/analytics placeholders noted for future enablement

---

## Maintenance

- [ ] Ops calendar: weekly backup verify, monthly restore drill
- [ ] Dependency update cadence agreed
- [ ] On-call / escalation contact listed in team vault

---

## Sign-off

| Role | Name | Date | Go / No-Go |
|------|------|------|------------|
| Engineering | | | |
| Ops / DevOps | | | |
| Product / Business | | | |
