# RTAS Studio AI

**Version 1.0.0** · **RC-2 Production Freeze** · Build `20260721.1`

**RTAS DIGITAL MARKETING COMPANY** · Under **RTAS GROUP OF COMPANIES**

International AI video SaaS: **Prompt to Video** and **Image to Video**.

> **Production freeze:** No new features on `master` after v1.0.0. Only hotfixes and verified patches.

**Live:** https://rtasstudio.com

## Stack (authoritative)

| Layer | Technology |
|-------|------------|
| Web | Next.js 14 (`apps/web`) on Vercel |
| Auth | NextAuth (credentials + Google) + password reset |
| Database | Prisma → Postgres (Supabase pooler) |
| Payments | Paddle (default) or Lemon Squeezy |
| Email | Resend (`rtasstudio.com` verified) |
| AI / GPU | FastAPI worker + fal.ai (tier routing) |
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

## Documentation

| Document | Path |
|----------|------|
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Deployment | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| API | [docs/API.md](docs/API.md) |
| Security | [docs/SECURITY.md](docs/SECURITY.md) |
| Release notes | [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md) |
| Known limitations | [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) |
| Backup & recovery | [docs/BACKUP_RECOVERY.md](docs/BACKUP_RECOVERY.md) |
| Environment | [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) |
| v1.0.0 engineering report | [docs/RTAS-STUDIO-AI-V1.0.0-ENGINEERING-REPORT.md](docs/RTAS-STUDIO-AI-V1.0.0-ENGINEERING-REPORT.md) |

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
- Password reset via signed email links (1-hour TTL)

## Legal

Terms: `/terms` · Privacy: `/privacy` · Refund: `/refund`
