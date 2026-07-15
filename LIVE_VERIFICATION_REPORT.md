# Live Production Verification Report

**Verified against:** https://rtas-studio-ai-web.vercel.app  
**Method:** Headless Edge (Playwright) viewport matrix + HTTP route checks + CSS/DOM inspection  
**Date:** 2026-07-16

## Failures found on live (pre-fix)

| # | Issue | Evidence |
|---|--------|----------|
| 1 | Header clips at 1024 / 1280 / 1366 | `headerMaxRight` 1333–1432 > viewport |
| 2 | Landing outcomes overlay transparent | `background: rgba(0,0,0,0)` |
| 3 | Hero overlay only 0.82 (target ≥0.88) | computed `rgba(0,0,0,0.82)` |
| 4 | Phase 1 CSS markers missing from live bundles | 0 matches for `drawer-nav`, `density-`, `0.88`, `studio-project-card` |
| 5 | React hydration errors #418 / #425 / #423 | console on production |
| 6 | Studio requires auth | `/studio` → `/auth/login` (expected for guests) |

## Passes

- No document horizontal overflow (scrollWidth === clientWidth) at tested widths
- Mobile 390 / tablet 768: no header clip
- Desktop 1440 / 1920: no header clip
- Nav/footer routes 200: features, pricing, docs, help, showcase, developers, careers, blog, status, privacy, terms, cookies, about, how-to-use

## Fixes in this redeploy

1. Raise pure-CSS + JS drawer breakpoint to **1440px** (hamburger below 1440)
2. Compact chrome 1440–1599 (hide credits CTA/meta, product subtitle)
3. Darken hero to **0.90** and section panels to **~0.82** glass
4. Auth header shows skeleton while session loading (hydration)
5. Safe SSR defaults: density compact + drawer on until measured

## Studio / autosave

Guided wizard + IndexedDB autosave are in repo (`StudioCreateExperience`, `studio-draft-files`). Live Studio UI is behind login; verify after sign-in: Choose project → Style → Title, refresh restores draft.
