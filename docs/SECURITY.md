# Security — RTAS Studio AI

Enterprise security baseline for the commercial web app and supporting services.

---

## Principles

1. **No secrets in git** — `.env.local`, `.env`, `.env.prisma*` are gitignored.
2. **Fail closed in production** — missing auth/payment/GPU config must not silently open unsafe paths.
3. **Least privilege** — service role / admin secrets server-only; never `NEXT_PUBLIC_*`.
4. **Rotate on exposure** — any key pasted into chat, email, or screenshots is compromised.
5. **Merchant of Record** — card data stays with Paddle/Lemon; never store PANs.

---

## Secret handling

| Do | Do not |
|----|--------|
| Store in Vercel Environment Variables | Commit `.env.local` |
| Use `apps/web/.env.production.example` placeholders | Hardcode keys in source |
| Rotate after leak | Share keys in Slack/Discord unencrypted |
| Scope GitHub PATs minimally | Put `SUPABASE_SERVICE_ROLE_KEY` in client bundles |

Generate strong secrets:

```bash
openssl rand -base64 32
```

---

## Auth security

- NextAuth credentials + Google OAuth.
- `allowDangerousEmailAccountLinking: false`.
- Google cannot take over an existing password account with the same email without proper linking policy (see `auth-options` / `upsertOAuthUser`).
- Production requires real `NEXTAUTH_SECRET`.
- Session-protected routes: `/studio`, `/profile` (middleware).
- Email verification flows via Resend/SMTP.

OAuth console must list **only** intended origins/redirects (see [INFRASTRUCTURE.md](./INFRASTRUCTURE.md)).

---

## API & webhook security

| Surface | Control |
|---------|---------|
| `/api/webhooks/paddle` | HMAC verify; fail closed if secret missing in production |
| `/api/webhooks/lemon-squeezy` | Signature verify; same posture |
| `/api/generate`, checkout, trial, compile, notify | Session / auth helpers (`api-auth.ts`) |
| `/api/admin/*` | `RTAS_ADMIN_SECRET` in production |
| Compile paths | Basename-only; path traversal hardened |
| Rate limiting | In-memory helper (upgrade to Redis/KV for multi-instance) |

---

## Transport & headers

Configured in root `vercel.json` / `apps/web/vercel.json`:

- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (camera/mic/geo disabled)
- API responses: `Cache-Control: no-store`

SSL for custom domains: Vercel-managed.

---

## Data

- Postgres via TLS (`sslmode=require` recommended).
- Prefer pooled `DATABASE_URL` for serverless.
- Supabase RLS required for any client-exposed tables.
- Vercel KV/Upstash for durable serverless state — treat tokens as secrets.
- Backups: [BACKUP.md](./BACKUP.md).

---

## Dependency & supply chain

- CI builds on clean `npm install` with lockfile.
- Pin Next.js; track advisories (`npm audit`). Known Next 14 CVEs may require upgrade path to 15/16 — document residual risk until upgraded.
- Do not commit `node_modules` or build artifacts with secrets.

---

## Admin & owner surfaces

- `RTAS_ADMIN_SECRET` for fal-funding admin APIs.
- `NEXT_PUBLIC_OWNER_EMAILS` is UI-only affordance — never sole authorization.

---

## Incident response (security)

1. Revoke/rotate exposed credentials (Google, fal, Resend, Vercel, Supabase, GitHub, DB password, Paddle webhook).
2. Invalidate sessions if `NEXTAUTH_SECRET` rotated (users re-login).
3. Review Vercel/GitHub audit logs.
4. Check Paddle for anomalous refunds/charges.
5. Restore from backup if data integrity suspect — [RECOVERY.md](./RECOVERY.md).

---

## Checklist before public launch

- [ ] All production secrets unique and not previously pasted in chat
- [ ] Google OAuth restricted to production (+ preview if needed)
- [ ] Webhook secrets set; test events verified
- [ ] `EMAIL_FROM` on verified domain (not Resend sandbox)
- [ ] `/api/ready` returns 200 on production
- [ ] Branch protection + required CI checks
- [ ] No secrets in client bundles (`NEXT_PUBLIC_*` reviewed)
