# Notification System — RTAS Studio AI

**Phase:** 13 · Sprint 4

## Channels

| Channel | Default | Notes |
|---------|---------|-------|
| Transactional email | On (locked) | Auth, verification, password reset |
| Billing email | On | Payment / cancel notices |
| Product email | On | Video ready |
| Marketing email | Off | Newsletter / campaigns |
| In-app announcements / security / billing / maintenance | On | Header + prefs page |

## Surfaces

- Header bell: `HeaderNotifications` (account alerts + announcements)
- Preferences: `/profile/notifications` · `GET/PATCH /api/user/notifications`
- Model: `MarketingNotificationPreference`
- Announcements: `SystemAnnouncement` (+ static fallbacks)

## Integrity

No fabricated inbox volumes. Empty announcement lists fall back to static product tips only.
