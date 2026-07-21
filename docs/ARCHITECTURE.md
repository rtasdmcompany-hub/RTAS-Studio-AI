# RTAS Studio AI — Architecture (v1.0.0)

## Important (legal & technical)

We **do not copy** proprietary model provider source code. RTAS integrates **licensed APIs** and owns the **UX, billing, credits, watermark policy, and category workflows**.

## Stack

```
┌─────────────────────────────────────────────────────────┐
│  Web (Next.js 14) — apps/web on Vercel                    │
│  Auth · Studio · Profile · Admin · Marketing · SEO        │
└──────────────┬──────────────────────────────────────────┘
               │ BFF API routes (session / admin / webhooks)
┌──────────────▼──────────────────────────────────────────┐
│  Prisma → Supabase Postgres (transaction pooler :6543)   │
│  Redis/KV → rate limits, ephemeral stores                  │
│  Resend → verification + password reset emails             │
│  Paddle → MoR checkout + webhooks → credit grants          │
└──────────────┬──────────────────────────────────────────┘
               │ FASTAPI_URL
┌──────────────▼──────────────────────────────────────────┐
│  FastAPI GPU worker                                       │
│  Fal.ai tier routing (Economy / Enterprise)               │
└─────────────────────────────────────────────────────────┘
```

## Generation pipeline

1. User selects mode (prompt | image) + category + visual style.
2. Category fields validated (`packages/shared`).
3. Credit check + server-side generation guard.
4. Job queued (`GenerationJob` statuses: QUEUED → … → COMPLETED/FAILED).
5. Fal models selected by billing tier cost routing.
6. Progress / ETA polled by Studio UI.
7. Output URL returned; download gated by subscription entitlement.

## Credit math

- **1 credit = 1 second** of finished video (product rule).
- Tester / Standard / Premium quotas defined in `packages/shared` and backend catalog.
- Expiry applied on profile load; webhook grants on subscription activation.

## Auth

- NextAuth JWT (30-day maxAge).
- Credentials require verified email.
- Google OAuth cannot silently take over password accounts.
- Password reset: HMAC-signed token, 1-hour TTL, rate limited.

## Admin / ops

- `/admin` + `/api/admin/*` protected by `RTAS_ADMIN_SECRET`.
- Metrics from live Prisma aggregates (users, jobs, credit totals, MRR estimate).
- Login events written to `SystemLog`.

## Related docs

- `docs/DEPLOYMENT.md`, `docs/SECURITY.md`, `docs/API.md`, `docs/ACTIVE-STACK.md`
