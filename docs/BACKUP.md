# Backup — RTAS Studio AI

Backup strategy for production data and configuration. Execute when production DB exists; procedures are valid with placeholders today.

---

## What to back up

| Asset | Criticality | Owner |
|-------|-------------|-------|
| Postgres (Prisma data: users, jobs, billing state) | **Critical** | Supabase/Neon automated + manual snapshots |
| Vercel env vars | **Critical** | Export checklist from `.env.production.example` (values in password manager) |
| Vercel KV / Upstash data | High | Provider snapshots / export if available |
| Git repository | High | GitHub (primary) + mirror optional |
| GPU worker local outputs (if `STORAGE_MODE=local`) | Medium | Prefer S3/R2 in production |
| Paddle / Resend / fal dashboards | Medium | Provider-side history |

Application code is recovered from Git — not from server disks.

---

## Database (Supabase)

### Automated

1. Supabase Dashboard → **Database** → **Backups** (plan-dependent PITR / daily).
2. Confirm retention meets RPO (recommended: ≤ 24h for commercial launch; tighter if PITR available).

### Manual snapshot (pre-release / pre-migration)

1. Dashboard → create backup / download logical dump if offered.
2. Or from a secure admin machine:

```bash
# REPLACE_* only — never commit connection strings
pg_dump "$DATABASE_URL_DIRECT" --format=custom --file="rtas-postgres-$(date +%Y%m%d).dump"
```

Store dumps encrypted (password manager vault / S3 with SSE).

### Neon alternative

Use Neon branching + point-in-time recovery per Neon docs; document project ID in the ops vault.

---

## Configuration backup

1. Maintain a **private** password-manager record mirroring every key in `apps/web/.env.production.example`.
2. After any Vercel env change, update the vault the same day.
3. Do **not** store production `.env` files in the git repo or shared Drive folders.

---

## KV / Redis

- Vercel KV / Upstash: enable provider backups if offered.
- Treat KV as rebuildable for some caches; **auth-related durable keys** may need restore — test restore once before launch.

---

## Media / generation outputs

Production should use object storage (`S3_*` / R2 in `apps/backend/.env.example`) rather than local disk.

| Mode | Backup |
|------|--------|
| Local disk | rsync/snapshots of `LOCAL_OUTPUT_DIR` — not HA |
| S3/R2 | Bucket versioning + cross-region replication (optional) |

---

## Backup schedule (recommended)

| Cadence | Action |
|---------|--------|
| Continuous / daily | Provider DB backup |
| Weekly | Verify backup job succeeded (ops calendar) |
| Before schema change | Manual `pg_dump` or provider snapshot |
| Before major release | Snapshot DB + note Vercel deployment ID |
| Quarterly | Test restore into a staging project |

---

## Retention

- DB: per provider plan (document actual days in ops vault).
- Manual dumps: keep last 4 weekly + last 3 pre-release snapshots unless compliance requires longer.
- Destroy obsolete dumps securely.

---

## Verification

At least once before public launch:

1. Restore dump into a **non-production** database.
2. Point a preview app at it (isolated secrets).
3. Confirm login + one project row readable.
4. Record result in ops log.

See [RECOVERY.md](./RECOVERY.md) for restore steps.
