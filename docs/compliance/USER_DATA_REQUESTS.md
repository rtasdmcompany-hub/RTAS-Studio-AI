# User Data Requests — RTAS Studio AI

**Date:** 23 July 2026  

---

## Self-serve (signed-in)

| Action | UI | API |
|--------|----|-----|
| Download personal data | `/profile/privacy` | `GET /api/user/privacy/export` |
| Request deletion | `/profile/privacy` | `POST /api/user/privacy/deletion-request` |
| Session posture | `/profile/privacy` | `GET /api/user/privacy/sessions` |
| Email preferences | `/profile/notifications` | `GET/PATCH /api/user/notifications` |
| Cookie prefs | Privacy settings / banner | localStorage via consent helpers |

---

## Email channel

`privacy@rtasstudio.com` — identity verification required for email-only DSARs.

---

## Ops checklist (deletion)

1. Confirm ticket number and account email ownership.  
2. Check open billing / chargebacks with Paddle.  
3. Preserve records required by law/tax (typically up to 7 years where applicable).  
4. Delete or anonymize eligible personal data and studio assets.  
5. Reply to user with completion or lawful refusal basis.  
6. Never claim “instant delete” in customer communications.

---

## Rate limits

Export: 5 / hour / user · Deletion request: 3 / hour / user.
