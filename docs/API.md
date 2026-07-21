# API Overview — RTAS Studio AI v1.0.0

Canonical developer documentation also lives in [`docs/developer/API.md`](./developer/API.md) and the public pages `/developers` and `/docs`.

## Base URLs

| Environment | URL |
|-------------|-----|
| Production web | `https://rtasstudio.com` |
| Production GPU worker | Configured via `FASTAPI_URL` (Vercel API project) |

## Authentication

- **Session:** NextAuth JWT cookie (credentials or Google).
- **Protected app routes:** `/studio`, `/profile` (middleware).
- **API session:** `requireApiSession()` on mutating BFF routes.
- **Admin:** header `x-rtas-admin-secret` matching `RTAS_ADMIN_SECRET`.
- **Backend worker:** fail-closed backend secret (`require_backend_secret`).

## Public probes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness |
| GET | `/api/ready` | Dependency readiness (details with admin secret) |

## Auth APIs

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/auth/register` | Credentials signup + verification email |
| POST | `/api/auth/forgot-password` | Rate-limited reset email |
| POST | `/api/auth/reset-password` | HMAC token + new password |
| POST | `/api/auth/resend-verification` | Rate-limited |
| GET | `/api/auth/verify-email` | Token → redirect |
| * | `/api/auth/[...nextauth]` | NextAuth handlers |

## Billing

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/checkout` | Session required; Paddle transaction URL |
| POST | `/api/webhooks/paddle` | Signature verified |
| GET | `/api/payments/config` | Public client config |

## Generation

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/generate` | Credits + session + rate limit |
| GET | `/api/generate/jobs/[jobId]` | Status / progress / ETA |
| POST | `/api/generate/jobs/[jobId]/retry` | Retry failed job |
| POST | `/api/generate/jobs/[jobId]/cancel` | Cancel |

## Admin

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/admin/dashboard` | Admin secret |
| GET | `/api/admin/analytics` | Admin secret |
| GET | `/api/admin/fal-funding` | Admin secret |

## Webhooks

Configure Paddle notification endpoint:

`https://rtasstudio.com/api/webhooks/paddle`

See `docs/PAYMENTS-WEBHOOKS.md`.

## Rate limits

Applied per-IP (and often per-email) via Redis/KV when configured; in-memory fallback locally. Exceeded requests return **HTTP 429**.

## Errors

| Status | Meaning |
|--------|---------|
| 401 | Unauthenticated |
| 403 | Email not verified / forbidden |
| 400 | Validation |
| 429 | Rate limited |
| 500 / 503 | Server / deferred dependency |
