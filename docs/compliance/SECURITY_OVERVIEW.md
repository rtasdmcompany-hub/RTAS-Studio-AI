# Security Overview — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Date:** 23 July 2026  
**Public page:** `/security`  

**Integrity rule:** No SOC 2 / ISO / “security audit approved” claims without evidence.

---

## Implemented

| Control | Evidence |
|---------|----------|
| TLS in transit | Production HTTPS (hosting) |
| Authenticated sessions (NextAuth JWT) | `auth-options.ts` |
| Email verification gates on sensitive APIs | `requireApiSession` |
| Admin secret gating | `RTAS_ADMIN_SECRET` |
| Payment webhook signature verification | Paddle / Lemon Squeezy adapters |
| Rate limiting on sensitive routes | `checkRateLimitAsync` |
| Security Center (user-facing) | `/security` |
| Privacy settings (session posture) | `/profile/privacy` |

---

## Partial

| Control | Gap |
|---------|-----|
| Multi-device session list / remote revoke | JWT strategy — current browser only |
| Centralized SIEM | Structured logs / Sentry optional |

---

## Roadmap (not shipped)

- TOTP / passkey 2FA  
- SOC 2 Type I/II attestation  
- ISO 27001 certification  
- Formal penetration-test report publication  

---

## Suspicious activity

Users: sign out → reset password (if credentials) → email `support@rtasstudio.com`.  
Ops: see [operations/SECURITY_GOVERNANCE.md](../operations/SECURITY_GOVERNANCE.md).

---

## Related

- [USER_DATA_REQUESTS.md](./USER_DATA_REQUESTS.md)  
- [operations/SECURITY_GOVERNANCE.md](../operations/SECURITY_GOVERNANCE.md)  
- Pre-launch audit docs under `docs/` (historical; not a live certification stamp)
