# Known Limitations — RTAS Studio AI v1.0.0

**Status:** Production freeze (RC-2)  
**Last updated:** 2026-07-21

This document lists intentional limitations and external blockers. These are not treated as application defects for the v1.0.0 freeze.

---

## External / owner actions

| Limitation | Impact | Owner action |
|------------|--------|--------------|
| Paddle live checkout not enabled on seller account | Paid checkout may fail with “Checkout has not yet been enabled” | Complete Paddle onboarding / enable checkout in vendors dashboard |
| Fal.ai wallet balance | Live generation blocked when balance is empty | Top up Fal.ai account |
| Google Search Console not submitted | Indexing slower until sitemap submitted | Submit `https://rtasstudio.com/sitemap.xml` |
| Bing Webmaster verification | Optional discovery | Add `NEXT_PUBLIC_BING_SITE_VERIFICATION` after registration |

---

## Product / engineering (accepted for v1.0.0)

| Limitation | Notes |
|------------|-------|
| CSP is Report-Only | Enforcing CSP risks breaking Paddle/Google embeds; enforce in a post-1.0 patch after QA |
| JWT sessions are stateless | “Logout all devices” requires a future `sessionVersion` field |
| `/admin` UI is secret-gated in-browser | APIs require `x-rtas-admin-secret`; page itself is noindexed |
| Revenue MRR in admin is estimate | Derived from active tier × plan price, not Paddle ledger reconciliation |
| User-facing credit ledger UI | Credits shown on profile; full transaction history UI deferred |
| Feature flags / maintenance mode | Present in backend/schema; not fully wired as global web middleware |
| OpenAPI interactive docs | Developers page documents routes; full OpenAPI export deferred |
| Status service cards | Static “Operational” copy; live JSON probes available underneath |
| Lighthouse 95+ targets | Not fully measured on every viewport in this freeze |

---

## Explicitly out of scope for v1.0.0 freeze

- New product features
- UI redesign
- Business-logic pricing changes
- Breaking API changes

Post-freeze work must land on a new minor/patch branch after production monitoring.
