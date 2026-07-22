# Support Operations — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Related:** [docs/product/support-channels.md](../product/support-channels.md) · [STANDARD_OPERATING_PROCEDURES.md](./STANDARD_OPERATING_PROCEDURES.md) · [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md) · Legal `/refund` · `/terms` · `/trust-safety` (v1.1)

---

## 1. Mission

Help customers use RTAS Studio AI successfully: credits, generation, account access, and honest billing expectations under **Paddle Merchant of Record** — without over-promising enterprise ticket SLAs the team has not contracted.

---

## 2. Channels (live vs goal)

| Channel | Status | Entry |
|---------|--------|-------|
| Help Center | **Live** | `/help` |
| FAQ / Billing / Troubleshooting | **Live** | `/help/*` |
| Contact | **Live** | `/help/contact` · `/support` |
| Changelog | **Live** | `/help/changelog` |
| How to use | **Live** | `/how-to-use` |
| Feedback | **Live** (mailto) | `/feedback` |
| Email | **Live** | support@rtasstudio.com · contact@rtasstudio.com |
| Live chat FAQ widget | **Live** (marketing/studio shell) | In-product |
| Ticketing CRM | **Goal** | Replace pure mailto when CRM adopted |
| Community forum / Discord | **Goal** | Future |
| Video tutorial library | **Goal** | Expand from Help |

---

## 3. Support levels

| Level | Scope | Handler |
|-------|-------|---------|
| **L0 Self-serve** | Docs, FAQ, troubleshooting, how-to-use | Customer |
| **L1 General support** | Account help, how-to, non-critical bugs, billing questions | Ops Owner / support inbox |
| **L2 Technical** | Reproducible product defects, generation failures, auth/email | Ops Owner (engineering) |
| **L3 Critical** | SEV1 site/pay/security; widespread outage | Ops Owner continuous + vendors |
| **MoR** | Refunds, tax invoices, chargebacks | **Paddle** (RTAS assists with account/credit context) |

---

## 4. Severity model (support view)

| Severity | Customer impact | Internal target first response | Internal target mitigation intent |
|----------|-----------------|--------------------------------|-----------------------------------|
| **S1** | Cannot access product or pay when checkout is live; security | **≤ 4 business hours** | Continuous until workaround |
| **S2** | Generation or email broken for user with no workaround | **≤ 1 business day** | Fix or workaround in 2 business days |
| **S3** | Degraded experience; workaround exists | **≤ 2 business days** | Scheduled fix |
| **S4** | Question / cosmetic / feature request | **≤ 3 business days** | Backlog |

**Label:** These are **internal response time aims (RTAs)**, not published contractual SLAs, unless a signed enterprise agreement states otherwise.

**Business hours (default):** Sunday–Thursday or Monday–Friday operator working pattern in Pakistan time (UTC+5) — state clearly in replies if delayed for weekends/holidays.

---

## 5. Escalation

1. L0 links in first reply when appropriate.  
2. L1 gathers reproduction data (SOP-01).  
3. L2 if defect confirmed.  
4. L3 / Ops Manual incident path for SEV1-class events.  
5. Paddle for MoR financial remedies.  
6. Trust & Safety path for AUP/abuse (SOP-10).

---

## 6. Communications standards

| Do | Do not |
|----|--------|
| Use clear English; confirm understanding | Promise ISO/SOC2 or uptime % you have not contracted |
| State MoR/refund path accurately | Ask for full card numbers |
| Distinguish “checkout pending approval” vs “Paddle outage” | Blame users for provider outages without checking |
| Offer Help Center links | Share internal secrets or admin URLs |
| Document goodwill credit grants | Violate Terms with unrestricted refunds |

**Tone:** Professional, calm, brand-consistent with RTAS Studio AI. No deepfake/face-swap assistance.

---

## 7. Customer expectations (truthful)

Customers can expect:

- Self-serve documentation on rtasstudio.com  
- Email support on published addresses  
- Legal policies v1.1 covering terms, privacy, refund, cookies, AI policy, trust & safety  
- Credits model: Tester $5 / 30 seconds / 5 days; Standard $89/mo / 2000 seconds; Premium 4K $249/mo / 2000 seconds; 1 credit = 1 second  

Customers should **not** assume:

- 24×7 phone support  
- Dedicated CSM unless sold separately  
- Contractual SLA credits for downtime (unless signed)  
- That live checkout is available if Paddle domain/checkout approval is still pending — support must verify current MoR status before asserting payment works  

---

## 8. Billing & credits playbook (support)

1. Confirm plan and approximate credit balance symptoms.  
2. Explain MoR: Paddle charges; RTAS provisions credits after successful webhook/fulfillment.  
3. Refund eligibility: point to `/refund` and Paddle process.  
4. Failed generation with charged credits: investigate per SOP-02 before manual restore.  
5. Never invent promotional pricing that contradicts live `/pricing`.

---

## 9. Metrics (manual until CRM)

| Metric | Cadence |
|--------|---------|
| Tickets received / closed | Weekly |
| Median first response | Weekly |
| S1 count | Monthly |
| Top contact drivers | Monthly |
| Escalations to incident | Monthly |

---

## 10. Handoffs to sales / enterprise

If inquiry is procurement, DPA, SSO, or security questionnaire: route to enterprise sales materials from Phase 11 (`docs/business/sales/*`, `docs/sales/*`) and [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) honesty rules — do not invent certifications in support email.

**Owner:** Ops Owner · **Review:** Quarterly · **Phase 11 Sprint 6**
