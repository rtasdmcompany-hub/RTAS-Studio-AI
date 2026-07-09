# RTAS Desktop

Electron shell for RTAS Studio AI. Loads the web studio (`@rtas/web`) in a native window — no duplicated frontend source.

## Dev

```bash
# Terminal 1 — web app
npm run dev:web

# Terminal 2 — desktop shell
npm run dev:desktop
```

Set `WEB_APP_URL=http://localhost:3000/studio` to override the default dev URL.

Production builds load `https://rtas-studio-ai-web.vercel.app/studio` unless `WEB_APP_URL` is set.
