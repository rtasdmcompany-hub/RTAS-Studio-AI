# RTAS Studio AI — Monorepo

Turborepo workspace: applications under `apps/`, shared code under `packages/`.
Every piece of reusable logic lives in a `@rtas/*` package and is consumed through a
package import or a thin re-export shim — **no source is duplicated across apps.**

## Apps

| App | Package | Port | Role |
|-----|---------|------|------|
| `apps/web` | `@rtas/web` | 3000 | User-facing Next.js studio, marketing, auth, BFF APIs, Prisma |
| `apps/backend` | `@rtas/backend` | 8000 | FastAPI GPU generation/upload/health (Python — not a JS package) |
| `apps/admin` | `@rtas/admin` | 3002 | Owner dashboard (Fal pool UI, admin proxies) |
| `apps/omni-reach` | `@rtas/omni-reach` | 3001 | Separate Omni Reach product (Next.js) |
| `apps/desktop` | `@rtas/desktop` | — | Electron shell around `@rtas/web` |
| `apps/rtas-mobile` | `@rtas/rtas-mobile` | — | Capacitor iOS/Android shell (remote web URL) |
| `apps/mobile` | `@rtas/mobile` | — | Expo WebView prototype |

## Shared packages

| Package | Import(s) | Purpose |
|---------|-----------|---------|
| `@rtas/shared` | `@rtas/shared` | Framework-agnostic domain: types, credits, categories, payments constants, video-pipeline math, legal content |
| `@rtas/types` | `@rtas/types` | Cross-cutting TS types (domain, pipeline, fal, identity) |
| `@rtas/utils` | `@rtas/utils`, `@rtas/utils/payments`, `@rtas/utils/server` | Pure utilities + payments parsers + server data layer (Prisma singleton, persistent store, data-dir) |
| `@rtas/ui` | `@rtas/ui`, `@rtas/ui/skeletons`, `@rtas/ui/css/components.css` | React design-system components + skeletons + brand lockups |
| `@rtas/icons` | `@rtas/icons` | Platform icons + brand asset metadata |
| `@rtas/hooks` | `@rtas/hooks` | Shared React hooks (`useUserVideoGallery`) |
| `@rtas/design-tokens` | `@rtas/design-tokens`, `@rtas/design-tokens/css/*`, `@rtas/design-tokens/tailwind/preset` | Colors, typography (Inter), spacing, radius, elevation, motion |
| `@rtas/config` | `@rtas/config/tsconfig` | Base `tsconfig` inherited by every app/package |

### Package export surface

- `@rtas/utils` (root barrel): `user-display-name`, `share-links`, `device-fingerprint`, `pipeline-errors`, `gallery-display`
- `@rtas/utils/payments`: `plan-detect`, `paddle`, `lemon-squeezy`
- `@rtas/utils/server`: `data-dir`, `persistent-store`, `prisma`
- `@rtas/ui`: `Button`, `Card`, `Dialog`, `Badge`, `ProgressBar`, `Alert`, `Spinner`, `EmptyState`, `BrandLogo`, `BrandLockup`, form fields, `lib/cn`
- `@rtas/ui/skeletons`: `SkeletonBar`, `GlassSkeletonPanel`, `AuthSkeleton`, `AuthLinkSkeleton`, `StudioSkeleton`, `ShimmerSkeleton`
- `@rtas/icons`: `PlatformIcon`, brand assets
- `@rtas/hooks`: `useUserVideoGallery`

## Moved files (source of truth → package)

Reusable logic was consolidated into packages. The canonical location for each is:

| Canonical package file | Domain |
|------------------------|--------|
| `packages/utils/src/user-display-name.ts` | `headerUserLabel`, `profileDisplayName` |
| `packages/utils/src/share-links.ts` | Public share URL/message builders, clipboard |
| `packages/utils/src/device-fingerprint.ts` | `getDeviceFingerprint` |
| `packages/utils/src/pipeline-errors.ts` | `PipelineFailureError` + guards (single class → safe `instanceof`) |
| `packages/utils/src/gallery-display.ts` | Gallery display item mapping/merging |
| `packages/utils/src/payments/plan-detect.ts` | Plan/variant → credits/billing resolution |
| `packages/utils/src/payments/paddle.ts` | Paddle webhook verify/parse + checkout config |
| `packages/utils/src/payments/lemon-squeezy.ts` | Lemon Squeezy webhook verify/parse + checkout config |
| `packages/utils/src/server/prisma.ts` | Prisma client singleton + `isPrismaConfigured` |
| `packages/utils/src/server/persistent-store.ts` | Redis/local JSON document store |
| `packages/utils/src/server/data-dir.ts` | `isServerlessRuntime` runtime detection |
| `packages/ui/src/*` | Design-system components, skeletons, brand lockups |
| `packages/icons/src/PlatformIcon.tsx`, `brand-assets.ts` | Platform icons + brand assets |
| `packages/hooks/src/useUserVideoGallery.ts` | User video gallery hook |
| `packages/design-tokens/src/*` | Design tokens |

## Changed imports (app re-export shims)

To keep existing deep imports (`@/lib/...`, `@/components/...`, `@/hooks/...`) working
**unchanged**, the old app paths now re-export from the package. No caller had to change.

### `apps/web`

| App path (unchanged for callers) | Re-exports from |
|----------------------------------|-----------------|
| `src/lib/prisma.ts` | `@rtas/utils/server` (`prisma`, `isPrismaConfigured`) |
| `src/lib/server/persistent-store.ts` | `@rtas/utils/server` |
| `src/lib/server/data-dir.ts` | `@rtas/utils/server` (`isServerlessRuntime`) |
| `src/lib/device-fingerprint.ts` | `@rtas/utils` |
| `src/lib/share-links.ts` | `@rtas/utils` |
| `src/lib/gallery-display.ts` | `@rtas/utils` |
| `src/lib/user-display-name.ts` | `@rtas/utils` |
| `src/lib/pipeline-errors.ts` | `@rtas/utils` |
| `src/lib/brand-assets.ts` | `@rtas/icons` |
| `src/lib/payments/lemon-squeezy.ts` | `@rtas/utils/payments` |
| `src/lib/payments/paddle.ts` | `@rtas/utils/payments` |
| `src/components/BrandLogo.tsx` | `@rtas/ui` |
| `src/components/BrandLockup.tsx` | `@rtas/ui` |
| `src/components/ui/skeletons/index.ts` | `@rtas/ui/skeletons` (+ local `ProfileSkeleton`) |
| `src/hooks/useUserVideoGallery.ts` | `@rtas/hooks` |

### `apps/omni-reach`

| App path (unchanged for callers) | Re-exports from |
|----------------------------------|-----------------|
| `src/lib/prisma.ts` | `@rtas/utils/server` (`prisma`, `isPrismaConfigured`) |
| `src/lib/server/persistent-store.ts` | `@rtas/utils/server` (also fixed a broken `@/lib/server/data-dir` import) |
| `src/lib/payments/lemon-squeezy.ts` | `@rtas/utils/payments` |
| `src/lib/payments/paddle.ts` | `@rtas/utils/payments` |
| `src/lib/payments/plan-detect.ts` | `@rtas/utils/payments` |
| `src/components/PlatformIcon.tsx` | `@rtas/icons` |

### Removed

- `packages/utils/src/server/user-mappers.ts` — orphaned dead code (not in the `server` barrel, contained broken `@/` app-alias imports). Each app keeps its own `src/lib/server/user-mappers.ts` because the mapping **legitimately differs per product**.

## Intentionally NOT shared (per-app by design)

These diverge between products (e.g. Omni Reach is a tester-only publishing plan) and must
stay app-local: `store.ts`, `auth/auth-options.ts`, `server/profile-store.ts`,
`server/auth-users.ts`, `server/user-mappers.ts`, `payments/apply-subscription.ts`,
`payments/index.ts`, and each app's Prisma `schema.prisma`.

## Path aliases

Every app inherits `@rtas/config/tsconfig` and declares:

```jsonc
"paths": {
  "@/*": ["./src/*"],                                   // app-local source
  "@rtas/shared": ["../../packages/shared/src/index.ts"] // source resolution
}
```

All other `@rtas/*` packages resolve through npm-workspace symlinks to each package's
`package.json` `main`/`exports` (`./src/index.ts`), so TypeScript and Next.js compile the
real source directly. Because the symlink target lives under `packages/` (outside
`node_modules`), Next.js transpiles it without extra `transpilePackages` entries. Each app
lists the packages it uses under `dependencies`/`devDependencies`.

## Prisma note

`apps/web` and `apps/omni-reach` each own a `prisma/schema.prisma` but generate into the
shared `node_modules/@prisma/client` (last `prisma generate` wins). The shared
`@rtas/utils/server` Prisma singleton binds to whichever client is generated. Always run the
target app's `db:generate` (its `build` does this automatically) before typechecking or
building that app.

## Commands

```bash
npm run dev            # web + admin + desktop (turbo, parallel)
npm run dev:web        # studio frontend (apps/web)
npm run dev:backend    # FastAPI API (apps/backend)
npm run dev:admin      # admin dashboard (apps/admin)
npm run build          # turbo build: web + admin + omni-reach
npm run typecheck      # turbo typecheck across workspace
```

Functionality is unchanged — this document records a structural (import-path) refactor only.
