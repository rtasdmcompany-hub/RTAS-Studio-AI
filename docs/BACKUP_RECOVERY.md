# Backup & Recovery — RTAS Studio AI v1.0.0

## Backup surfaces

| Asset | Location | Backup method |
|-------|----------|---------------|
| Application source | GitHub `RTAS-Studio-AI` | Git remotes + protected `master` |
| Postgres data | Supabase project | Supabase automated backups / PITR (plan-dependent) |
| Redis / KV | Vercel KV / Upstash | Provider persistence; treat as ephemeral cache |
| Environment secrets | Vercel project env | Export via Vercel dashboard; never commit |
| User media / renders | Provider storage + app URLs | Follow Fal/storage retention; re-generate if lost |
| DNS | Hostinger zone for `rtasstudio.com` | Documented in `docs/RTASSTUDIO-COM-DNS.md` |

Related: `docs/BACKUP.md`, `docs/RECOVERY.md`, `docs/OPERATIONS.md`.

## Recovery procedures

### Application rollback
1. Identify last known-good commit / Vercel deployment.
2. Promote prior deployment in Vercel **or** revert commit and redeploy.
3. Smoke: `/api/health`, `/api/ready`, `/auth/login`, `/`.

### Database
1. Use Supabase dashboard → Backups / PITR for the project region.
2. Prefer restore to a new database first; validate with Prisma `db push` / migrate status.
3. Update `DATABASE_URL` / `DATABASE_URL_DIRECT` on Vercel only after validation.

### Secrets compromise
1. Rotate all exposed keys (NextAuth, DB, Google, Resend, Paddle, Fal, admin secret).
2. Sync to Vercel production/preview.
3. Redeploy web + API projects.
4. Invalidate sessions by rotating `NEXTAUTH_SECRET` (forces re-login).

### Domain / DNS
1. Restore Hostinger nameservers / zone from `docs/RTASSTUDIO-COM-DNS.md`.
2. Confirm Vercel domain verified + SSL.
3. Confirm Resend DKIM/SPF remain verified.

## RPO / RTO targets (operational)

| Metric | Target |
|--------|--------|
| RPO (data) | Provider backup window (typically ≤ 24h on free/pro tiers) |
| RTO (app) | < 1 hour via Vercel redeploy / rollback |
| RTO (DNS) | Propagation-dependent (minutes to hours) |

## Contacts

Ops owner: RTAS Digital Marketing Company  
Production domain: https://rtasstudio.com
