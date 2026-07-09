# Infrastructure placeholders — RTAS Studio AI

Production domain, API host, CDN, email domain, and webhook URLs are **not required yet**.
This document freezes the naming contract so go-live is a fill-in exercise.

Replace every `REPLACE_*` token when accounts are ready. Do not invent alternate paths without updating OAuth, webhooks, and env templates together.

---

## Domain map

| Role | Placeholder | Typical DNS |
|------|-------------|-------------|
| App (canonical) | `REPLACE_APP_DOMAIN` | `A`/`CNAME` → Vercel |
| WWW alias | `www.REPLACE_APP_DOMAIN` | Redirect → apex or vice versa |
| GPU / FastAPI | `api.REPLACE_APP_DOMAIN` | `CNAME` → GPU host / tunnel |
| CDN (future) | `cdn.REPLACE_APP_DOMAIN` | CDN provider |
| Assets (future) | `assets.REPLACE_APP_DOMAIN` | R2/S3/CDN |
| Email sending | `REPLACE_EMAIL_DOMAIN` | Often same as app apex |
| Preview | `*.vercel.app` | Automatic |

Suggested defaults (change only if brand requires):

```
App:     https://REPLACE_APP_DOMAIN
API:     https://api.REPLACE_APP_DOMAIN
CDN:     https://cdn.REPLACE_APP_DOMAIN
Mail:    noreply@REPLACE_EMAIL_DOMAIN
```

---

## Environment binding

When domains exist, set:

```bash
NEXT_PUBLIC_APP_URL=https://REPLACE_APP_DOMAIN
NEXTAUTH_URL=https://REPLACE_APP_DOMAIN
FASTAPI_URL=https://api.REPLACE_APP_DOMAIN
NEXT_PUBLIC_FASTAPI_URL=https://api.REPLACE_APP_DOMAIN
EMAIL_FROM="RTAS STUDIO AI <noreply@REPLACE_EMAIL_DOMAIN>"
# Optional:
# NEXT_PUBLIC_CDN_URL=https://cdn.REPLACE_APP_DOMAIN
# NEXT_PUBLIC_ASSETS_URL=https://assets.REPLACE_APP_DOMAIN
```

Backend (`apps/backend`):

```bash
CORS_ORIGINS=https://REPLACE_APP_DOMAIN,https://www.REPLACE_APP_DOMAIN
PUBLIC_BASE_URL=https://api.REPLACE_APP_DOMAIN
```

---

## Webhook URLs (register after first production deploy)

| Provider | URL |
|----------|-----|
| Paddle | `https://REPLACE_APP_DOMAIN/api/webhooks/paddle` |
| Lemon Squeezy | `https://REPLACE_APP_DOMAIN/api/webhooks/lemon-squeezy` |
| Generation worker → web | Configured via `RTAS_GENERATION_WEBHOOK_SECRET` on both sides |

---

## Google OAuth (register after domain)

| Setting | Value |
|---------|-------|
| Authorized JavaScript origins | `https://REPLACE_APP_DOMAIN` (+ www if used) |
| Authorized redirect URIs | `https://REPLACE_APP_DOMAIN/api/auth/callback/google` |

Mirror into `GOOGLE_OAUTH_JS_ORIGIN` and `GOOGLE_OAUTH_REDIRECT_URI`.

---

## DNS checklist (execute at go-live)

1. Add domain in Vercel → Domains (SSL automatic).
2. Point apex + www per Vercel DNS instructions.
3. Point `api` subdomain to GPU host (or reverse proxy).
4. Add Resend DNS (SPF, DKIM, optionally DMARC) for `REPLACE_EMAIL_DOMAIN`.
5. Wait for SSL + DNS propagation; then set env URLs and redeploy.
6. Update Paddle/Lemon webhook endpoints to HTTPS production URLs.
7. Update Google OAuth console entries.
8. Probe: `GET https://REPLACE_APP_DOMAIN/api/health` and `/api/ready`.

---

## CDN (future)

Not required for MVP. When enabled:

- Serve static marketing assets / generated media via `NEXT_PUBLIC_CDN_URL`.
- Keep API and auth cookies on the app origin only (no cross-site session cookies on CDN).
- Configure cache headers already present in `vercel.json` for `/_next/static`.

---

## Regions

Current Vercel config: `iad1` (see root `vercel.json`). Change only with latency/compliance review.
