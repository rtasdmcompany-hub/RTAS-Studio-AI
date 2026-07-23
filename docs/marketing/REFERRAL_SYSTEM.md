# Referral System — RTAS Studio AI

**Phase:** 13 · Sprint 4  
**Status:** UI + schema live · **Rewards = Proposed** (not auto-granted)

## User surfaces

- `/referral` — code, link, invite form, history
- `GET/POST /api/user/referral`

## Schema

- `StudioReferralCode` — per-user code + link
- `StudioReferral` — invite / signup / convert tracking

## Proposed rewards

| Party | Credits (Proposed) |
|-------|--------------------|
| Referrer | 30 |
| Referred | 15 |

Credits are **not** written to user balances until a dedicated reward engine is enabled.

## Related

Org-scoped Phase 8 `ReferralCode` / `Referral` models remain for enterprise affiliate engine; Studio consumer referrals use `StudioReferral*`.
