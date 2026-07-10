# Developer documentation

## Monorepo

See [MONOREPO.md](../../MONOREPO.md) and [ACTIVE-STACK.md](../ACTIVE-STACK.md).

## Local development

```bash
npm install
cp apps/web/.env.example apps/web/.env.local
npm run setup:env -w @rtas/web
npm run dev:web
```

## Quality gates

```bash
npm run lint -w @rtas/web
npm run typecheck -w @rtas/web
npm run test -w @rtas/web
npm run build -w @rtas/web
```

## Key packages

| Package | Role |
|---------|------|
| `@rtas/web` | Next.js SaaS app |
| `@rtas/ui` | Design system primitives |
| `@rtas/shared` | Plans, credits, legal |
| `@rtas/utils` | Payments verify, persistent store |
| `@rtas/backend` | FastAPI GPU worker |

## Architecture

[ARCHITECTURE.md](../ARCHITECTURE.md) · [AI-SERVICE.md](../AI-SERVICE.md)

## Environment

[ENVIRONMENT.md](../ENVIRONMENT.md) — never commit secrets.
