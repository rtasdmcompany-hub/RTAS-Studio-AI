# RTAS Studio AI

**RTAS DIGITAL MARKETING COMPANY** · Under **RTAS GROUP OF COMPANIES**

International AI video SaaS: **Prompt to Video** and **Image to Video**.

## Stack (authoritative)

| Layer | Technology |
|-------|------------|
| Web | Next.js 14 (`apps/web`) on Vercel |
| Auth | NextAuth (credentials + Google) |
| Database | Prisma → Postgres (Supabase/Neon) |
| Payments | Paddle (default) or Lemon Squeezy |
| Email | Resend (or SMTP) |
| AI / GPU | FastAPI worker + fal.ai |
| Persistence | Vercel KV / Upstash Redis |

See `MONOREPO.md` and `docs/ACTIVE-STACK.md`.

## Quick start

```bash
cd "RTAS Studio AI"
npm install
cp apps/web/.env.example apps/web/.env.local
# Fill secrets — see docs/ENVIRONMENT.md
npm run setup:env -w @rtas/web   # optional secret bootstrap
npm run dev:web
```

Open http://localhost:3000

GPU worker (optional locally):

```bash
npm run dev:api
```

## Production deploy (when credentials are ready)

1. Fill `apps/web/.env.production.example` → Vercel env for project **rtas-studio-ai-web**
2. Link Vercel KV
3. Add domain + DNS
4. Deploy
5. Smoke: `/api/health`, `/api/ready`

Full runbooks:

- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/RELEASE-CHECKLIST.md](docs/RELEASE-CHECKLIST.md)
- [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/RELEASE-REPORT.md](docs/RELEASE-REPORT.md)

## Quality gates

```bash
npm run verify:deployment-ready -w @rtas/web
npm run lint -w @rtas/web
npm run typecheck -w @rtas/web
npm run test -w @rtas/web
npm run verify:production -w @rtas/web
npm run build -w @rtas/web
```

## Product rules (implemented)

- Free trial path with abuse controls
- Paid plans via Merchant of Record (Paddle / Lemon Squeezy)
- Credits + commercial license entitlement on active subscription
- Server-side generation gateway (clients cannot bypass billing)

## Legal

Terms: `/terms` · Privacy: `/privacy`
