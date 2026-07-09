# Recovery & rollback — RTAS Studio AI

Procedures to restore service after a bad deploy, data incident, or dependency outage.

---

## Severity guide

| Level | Example | First action |
|-------|---------|--------------|
| SEV1 | Site down / payments broken / data loss | Rollback deploy or restore DB; status comms |
| SEV2 | Email or GPU degraded | Failover config; monitor |
| SEV3 | Non-critical UI bug | Patch forward via PR |

---

## A. Application rollback (Vercel) — fastest

**Target RTO:** minutes.

1. Vercel → Project → **Deployments**.
2. Locate last known-good production deployment (note ID in ops log).
3. **⋯ → Promote to Production** (or Redeploy that commit).
4. Verify:
   - `GET https://REPLACE_APP_DOMAIN/api/health`
   - `GET https://REPLACE_APP_DOMAIN/api/ready`
   - Login + Studio load
5. If env caused the outage: fix variables → **Redeploy** (Promote alone may keep bad env).

Git rollback (optional):

```bash
git revert <bad-commit>
git push origin main
```

Prefer Vercel promote for immediate traffic shift; follow with git revert for history clarity.

---

## B. Environment misconfiguration

1. Compare Vercel env to `apps/web/.env.production.example`.
2. Restore values from password vault ([BACKUP.md](./BACKUP.md)).
3. Redeploy production.
4. Run `npm run probe:services -w @rtas/web` against production-shaped env.

---

## C. Database restore

**Only with explicit approval** — overwrites data.

1. Put app in maintenance if possible (Vercel deployment pause / middleware flag — or announce downtime).
2. Supabase → restore backup / PITR to target timestamp **or** `pg_restore` into a new database then swap `DATABASE_URL`.
3. Update `DATABASE_URL` in Vercel if host changed.
4. Redeploy / restart.
5. Verify user login and recent rows.
6. Re-check Paddle webhooks for events during the outage window (replay if provider supports).

---

## D. Payment webhook recovery

1. Confirm `PADDLE_WEBHOOK_SECRET` matches Paddle dashboard.
2. Paddle → webhook logs → replay failed events to  
   `https://REPLACE_APP_DOMAIN/api/webhooks/paddle`.
3. Confirm subscription entitlements in app DB / profile.

---

## E. GPU worker recovery

1. Check `https://api.REPLACE_APP_DOMAIN/api/health` (or worker host).
2. Restart worker process/container.
3. Confirm `FASTAPI_URL` and `CORS_ORIGINS`.
4. Confirm `FAL_KEY` / credits.
5. Web `/api/ready` should show `fastApi.ok` once URL is reachable (readiness checks config; worker liveness is separate).

---

## F. Email recovery

1. Resend dashboard → domain status + API key validity.
2. Rotate `RESEND_API_KEY` if unauthorized.
3. Ensure `EMAIL_FROM` uses verified domain.
4. SMTP fallback: set `SMTP_*` and redeploy.

---

## G. Secret compromise

1. Rotate **all** exposed secrets (see [SECURITY.md](./SECURITY.md)).
2. Rotate `NEXTAUTH_SECRET` → all sessions invalidate (expected).
3. Rotate DB password → update `DATABASE_URL` → redeploy.
4. Revoke GitHub PAT / Vercel token if leaked.
5. Audit recent admin and billing activity.

---

## H. Communication template

```
RTAS Studio AI status: investigating / identified / monitoring
Impact: <login | generate | checkout | email>
Next update: <time>
```

---

## Post-incident

1. Timeline + root cause.
2. Action items (tests, alerts, runbook gaps).
3. Update [OPERATIONS.md](./OPERATIONS.md) / this file if steps were wrong.
