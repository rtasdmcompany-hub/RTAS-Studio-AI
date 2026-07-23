# Data Privacy — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Date:** 23 July 2026  
**Public pages:** `/privacy` · `/profile/privacy` · `/compliance`  

---

## Controller

RTAS Digital Marketing Company acts as controller for account and Service usage data. Payment card data is processed by Paddle (MoR).

---

## Rights & channels

| Right | Channel | Status |
|-------|---------|--------|
| Access / portability | `/profile/privacy` → Download my data · or `privacy@rtasstudio.com` | Implemented |
| Deletion / erasure | Deletion request ticket · or email | Implemented (review workflow, not instant wipe) |
| Rectification | Account profile / support | Partial (email + account fields) |
| Cookie consent withdraw | Banner / Privacy settings / Cookie Policy | Implemented |
| Marketing email opt-out | `/profile/notifications` | Implemented |

---

## Export contents

JSON export includes account metadata, projects, generation jobs (capped), support tickets, notification preferences. **Never** includes password hashes or full card numbers.

API: `GET /api/user/privacy/export`

---

## Deletion workflow

1. User submits confirm from Privacy settings.  
2. High-priority `account` support ticket created.  
3. Email notification to `privacy@rtasstudio.com` when mail is configured.  
4. Ops verifies identity, applies statutory/billing retention, then erases or anonymizes eligible data.  

Typical timeline: 30–45 days (policy language).

API: `POST /api/user/privacy/deletion-request`

---

## Framework readiness

Practices are designed to **align with** GDPR / UK GDPR / CCPA expectations. This is **readiness**, not certification.
