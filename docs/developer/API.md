# API documentation (web)

Base: same origin as the Next.js app.

## Public

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/health` | Liveness |
| GET | `/api/ready` | Readiness (minimal public body) |
| GET | `/api/auth/config` | Public runtime flags |
| GET | `/api/payments/config` | Public payment config |
| GET | `/api/share/[videoId]` | Public share payload |

## Authenticated (session)

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/generate` | Credit-guarded generation |
| POST | `/api/upload` | Asset upload gateway |
| POST | `/api/compile` | Clip compile |
| POST | `/api/checkout` | Start MoR checkout |
| POST | `/api/notify/video-ready` | Email notify |
| POST | `/api/share/[videoId]` | Publish share (URL allowlist) |

## Auth

| Method | Path | Notes |
|--------|------|-------|
| * | `/api/auth/[...nextauth]` | NextAuth |
| POST | `/api/auth/register` | Rate limited |
| POST | `/api/auth/resend-verification` | Rate limited |
| POST | `/api/auth/check-verification` | No password (non-oracle) |

## Webhooks

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/webhooks/paddle` | Signed; fail-closed |
| POST | `/api/webhooks/lemon-squeezy` | Signed; fail-closed |

Admin routes require `x-rtas-admin-secret`.
