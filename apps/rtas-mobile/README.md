# RTAS Studio AI — Capacitor Mobile Shell

Isolated native wrapper for **iOS** and **Android**. Loads the live production web app at:

**https://rtas-studio-ai-web.vercel.app**

No files under `apps/web` are modified. This module is independent of the Vercel build.

## Brand assets (icons + splash)

Drop master artwork, then generate all native sizes:

```bash
# 1. Drop your file:
#    apps/rtas-mobile/assets/icons/logo-master.png  (1024×1024+)

# 2. Generate iOS + Android icon/splash densities:
npm run mobile:assets

# 3. Open Android Studio:
npm run mobile:android
```

See `assets/README.md` for full drop-zone layout and generation modes.

## Quick start

```bash
# From monorepo root
npm install
npm run sync -w @rtas/rtas-mobile
npm run open:android -w @rtas/rtas-mobile   # requires Android Studio
npm run open:ios -w @rtas/rtas-mobile       # requires Xcode (macOS)
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run sync -w @rtas/rtas-mobile` | Copy web assets + update native projects |
| `npm run open:android -w @rtas/rtas-mobile` | Open Android Studio |
| `npm run open:ios -w @rtas/rtas-mobile` | Open Xcode |

## Configuration

- **`capacitor.config.ts`** — `server.url` points to the live Vercel deployment.
- **`www/`** — Offline fallback shell with safe-area viewport rules (used when not on remote server mode).
- **`assets/icons/`**, **`assets/splash/`** — Placeholder paths for store-ready artwork.

## Store submission checklist

1. Replace icon/splash placeholders under `assets/`.
2. Run `@capacitor/assets generate`.
3. Set signing teams in Xcode / Android Studio.
4. Test auth, uploads, and generation on physical devices.
