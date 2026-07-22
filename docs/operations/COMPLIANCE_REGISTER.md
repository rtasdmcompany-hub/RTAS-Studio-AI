# Compliance Register — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Merchant of Record:** Paddle (checkout/domain activation may still be pending — verify live status)  
**Legal suite:** **v1.1** APPROVED / live (effective 22 July 2026 per legal sign-off)  
**Effective register date:** 22 July 2026  

**Related:** [docs/LEGAL_DOCUMENTATION_SIGNOFF.md](../LEGAL_DOCUMENTATION_SIGNOFF.md) · [docs/LEGAL_POLICY_AUDIT_v1.1.md](../LEGAL_POLICY_AUDIT_v1.1.md) · [docs/PADDLE_COMPLIANCE_REPORT.md](../PADDLE_COMPLIANCE_REPORT.md) · [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) · [business/legal/README.md](../../business/legal/README.md)

---

## 1. How to read this register

| Status | Meaning |
|--------|---------|
| **Implemented** | Live control, policy, or page exists |
| **Partial** | Some controls exist; gaps remain |
| **Goal** | Desired future state — **not** claimed as done |
| **N/A** | Not applicable at current stage |

**Certification rule:** Entries never invent ISO, SOC 2, or “GDPR certified” status for RTAS Studio AI.

---

## 2. Register

| ID | Area | Obligation / control | Status | Evidence / location | Owner | Review cadence | Next review |
|----|------|----------------------|--------|---------------------|-------|----------------|-------------|
| C-01 | Privacy | Public Privacy Policy; controller/operator disclosure; MoR payment processing disclosure | **Implemented** | https://rtasstudio.com/privacy · legal v1.1 | Ops Owner | Quarterly or on material processing change | Oct 2026 |
| C-02 | AI use | AI Usage Policy — original/licensed/owned/authorized content only | **Implemented** | https://rtasstudio.com/ai-policy | Ops Owner | Quarterly | Oct 2026 |
| C-03 | Trust & Safety | Prohibitions: face-swap, celebrity impersonation, deepfake abuse, etc. | **Implemented** | https://rtasstudio.com/trust-safety | Ops Owner | Quarterly + after AUP incidents | Oct 2026 |
| C-04 | Terms / AUP | Terms of Service incl. Prohibited Uses & Acceptable Use (§10) | **Implemented** | https://rtasstudio.com/terms | Ops Owner | Quarterly | Oct 2026 |
| C-05 | Refunds | Refund policy aligned with Paddle MoR | **Implemented** | https://rtasstudio.com/refund | Ops Owner | Quarterly | Oct 2026 |
| C-06 | Cookies | Cookie notice / consent framing + third-party payment cookies disclosure | **Implemented** | https://rtasstudio.com/cookies | Ops Owner | Quarterly | Oct 2026 |
| C-07 | Merchant of Record | Paddle as MoR for card processing/tax/refunds | **Implemented (policy)** · **Partial (checkout execution)** | Legal pages · Paddle dashboard | Ops Owner | Weekly while gated · Monthly when live | Ongoing |
| C-08 | Security baseline | Headers, auth, webhook verify, secrets hygiene, audits | **Implemented (baseline)** | `docs/SECURITY.md` · pre-launch audit docs | Ops Owner | Quarterly | Oct 2026 |
| C-09 | Data Protection / DPD posture | Privacy disclosures + MoR; international transfer language in policy | **Partial** | Privacy policy; operator in Pakistan | Ops Owner | Quarterly | Oct 2026 |
| C-10 | GDPR certification | Formal certification / audited GDPR program | **Goal / Not claimed** | — | Ops Owner | Annual strategy | Jul 2027 |
| C-11 | SOC 2 | Type I/II attestation | **Goal / Not claimed** | — | Ops Owner | Annual strategy | Jul 2027 |
| C-12 | ISO 27001 | ISMS certification | **Goal / Not claimed** | — | Ops Owner | Annual strategy | Jul 2027 |
| C-13 | Customer DPA template | Standard enterprise DPA pack | **Goal** | Enterprise sales future | Ops Owner | Semi-annual | Jan 2027 |
| C-14 | Open-source licenses | Respect dependency licenses; lockfile CI | **Partial** | Repo license files + npm packages | Ops Owner | Semi-annual | Jan 2027 |
| C-15 | Marketing claims | No deepfake/face-swap marketing; Identity Preservation = authorized only | **Implemented** | Paddle compliance report · live site | Ops Owner | Monthly spot-check | Aug 2026 |
| C-16 | Pricing honesty | Public pricing matches credit model | **Implemented** | `/pricing` · shared credits constants | Ops Owner | On every pricing change | Event-driven |
| C-17 | Email / messaging compliance | Transactional mail via Resend; domain auth | **Partial–Implemented** | Resend + DNS docs | Ops Owner | Monthly | Aug 2026 |
| C-18 | Children / age | Per Terms/Privacy (no child-directed product positioning) | **Implemented (policy)** | Legal v1.1 | Ops Owner | Annual | Jul 2027 |
| C-19 | Export / sanctions screening | No automated sanctions platform claimed | **Goal / manual diligence** | Sales process when needed | Ops Owner | Semi-annual | Jan 2027 |
| C-20 | Accessibility (legal pages) | Documented a11y pass in legal sign-off | **Partial** | Legal sign-off scores | Ops Owner | On legal redesign | Event-driven |

---

## 3. Pakistan / international note

Operator operates from Pakistan; product is offered globally via web. Privacy and Terms state entity and MoR relationships. Local regulatory evolution (including data protection developments relevant to Pakistan and target customer jurisdictions) is monitored as a **Partial** ongoing duty — not a claim of multi-jurisdiction certification.

---

## 4. Paddle / AUP coupling

Paddle previously raised AUP concerns around face-swap / impersonation framing. Remediation and Trust & Safety / AI Policy publication are documented in `docs/PADDLE_COMPLIANCE_REPORT.md`. Compliance posture for MoR requires **ongoing marketing discipline**, not a one-time copy edit.

---

## 5. Review ritual

1. Open this register.  
2. Verify each **Implemented** row still matches the live site and dashboards.  
3. Update C-07 with honest checkout/approval status.  
4. Move any completed Goals only with evidence.  
5. File findings in quarterly ops notes and Risk Register if gaps are material.

**Owner:** Ops Owner · **Phase 11 Sprint 6**
