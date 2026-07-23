# Cookie Management — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Date:** 23 July 2026  
**Policy:** `/cookies` · **UI:** cookie banner + `/profile/privacy`  

---

## Categories

| Category | Default | Behavior |
|----------|---------|----------|
| Necessary | Always on | Auth, CSRF, consent storage, core studio prefs |
| Analytics | Off until opt-in | Gates `trackClientEvent` / optional analytics |
| Marketing | Off until opt-in | Gates marketing tags when configured |

Storage key: `rtas-cookie-consent` (JSON prefs; legacy `"all"` / `"essential"` still read).

Code: `apps/web/src/lib/analytics/consent.ts` · `CookieConsent.tsx`

---

## User flows

1. First visit → banner: Necessary only · Accept all · Manage preferences.  
2. Manage preferences → toggles for Analytics / Marketing.  
3. Withdraw → turn categories off in Privacy settings or reopen banner via Cookie settings.  
4. Optional trackers must not load before consent (`hasAnalyticsConsent` / `hasMarketingConsent`).

---

## Vendor scripts

Sprint 4 analytics uses consent-gated structured logging and optional `dataLayer` push. Third-party pixels are **not** auto-injected solely because env IDs exist — ops must add Script tags consciously and still respect consent.

---

## Related

- [LEGAL_COMPLIANCE.md](./LEGAL_COMPLIANCE.md)  
- Cookie Policy copy: `packages/shared/src/legal/cookies.ts`
