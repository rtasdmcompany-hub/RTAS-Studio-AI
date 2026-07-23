# Legal Compliance — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company  
**Document version:** 1.0 · **Date:** 23 July 2026  
**Legal suite:** v1.2 (Last Updated 23 July 2026)  

**Integrity rule:** This document describes policy pages and operational readiness. It does **not** claim GDPR certification, SOC 2, ISO 27001, or external legal counsel sign-off unless separately evidenced.

---

## 1. Public legal surfaces

| Page | URL | Status |
|------|-----|--------|
| Terms of Service (incl. AUP §10) | `/terms` | Implemented |
| Privacy Policy | `/privacy` | Implemented |
| Cookie Policy | `/cookies` | Implemented |
| Refund Policy | `/refund` | Implemented |
| AI Usage Policy | `/ai-policy` | Implemented |
| Trust & Safety | `/trust-safety` | Implemented |
| Community Guidelines | `/community-guidelines` | Implemented (Sprint 8) |
| Copyright & DMCA | `/dmca` | Implemented (Sprint 8) |

Shared copy: `packages/shared/src/legal/*` · Chrome: `LegalLayout` / `LegalProse`.

---

## 2. Contact consistency

| Alias | Use |
|-------|-----|
| `support@rtasstudio.com` | Product support |
| `contact@rtasstudio.com` | General |
| `legal@rtasstudio.com` | Legal / DMCA / disputes |
| `privacy@rtasstudio.com` | Privacy / DSAR |
| `info@rtasstudio.com` | General info (site-links) |

Constants: `apps/web/src/lib/site-links.ts` · `LEGAL_*_EMAIL` in `packages/shared/src/legal/terms.ts`.

---

## 3. Merchant of Record

Paddle is disclosed as MoR for paid checkout, tax, invoices, and refunds. RTAS Digital Marketing Company operates the product; it is not the card acquirer.

---

## 4. Related

- [LEGAL_DOCUMENTATION_SIGNOFF.md](../LEGAL_DOCUMENTATION_SIGNOFF.md) (v1.1 freeze; Sprint 8 additive v1.2)
- [DATA_PRIVACY.md](./DATA_PRIVACY.md)
- [COOKIE_MANAGEMENT.md](./COOKIE_MANAGEMENT.md)
- [operations/COMPLIANCE_REGISTER.md](../operations/COMPLIANCE_REGISTER.md)
