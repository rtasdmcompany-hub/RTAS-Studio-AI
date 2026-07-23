# Founder Operations Checklist — RTAS Studio AI

**Operator:** RTAS Digital Marketing Company  
**Date:** 23 July 2026  
**Extends:** [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md) · [SUPPORT_OPERATIONS.md](./SUPPORT_OPERATIONS.md) · [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) · [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md)

Founder-operated SaaS cadence. Times are UTC+5 (Pakistan) unless noted.

---

## Daily

| # | Check | How | Pass |
|---|-------|-----|------|
| 1 | Site liveness | `GET /api/health` | `200` ok |
| 2 | Readiness | `GET /api/ready` | `200` ready (investigate `503`) |
| 3 | Status summary | `/status` + `/api/status/summary` | Labels match expected config |
| 4 | Deploy health | Vercel production deploy | No unexplained failed deploy |
| 5 | Support inbox | `support@` / `contact@` / tickets | Triage Sev-1 same day |
| 6 | Privacy / deletion tickets | Support category `account` + `privacy@` | Ack new DSARs |
| 7 | Payments | Paddle dashboard (when live) | Webhook failures investigated |
| 8 | AI balance | Fal / Replicate (when generating) | Sufficient balance |

---

## Weekly

| # | Check | Notes |
|---|-------|-------|
| 1 | Incident log | Add real incidents to `/status` history only |
| 2 | Cookie / analytics | Confirm optional vendors still consent-gated |
| 3 | Legal link spot-check | Terms / Privacy / Refund / Cookies / DMCA / Security / Compliance |
| 4 | Backup / recovery skim | Confirm DB backups / host snapshots per BCP |
| 5 | Revenue snapshot | MRR / new subs / refunds (Paddle) — no fabricated metrics |
| 6 | Security review lite | Failed login spikes, admin secret rotation if shared |

---

## Monthly

| # | Check | Notes |
|---|-------|-------|
| 1 | Compliance register | Update [COMPLIANCE_REGISTER.md](./COMPLIANCE_REGISTER.md) statuses honestly |
| 2 | Access review | Who has Vercel, Paddle, Resend, GitHub, DB |
| 3 | Retention / DSAR backlog | Close or escalate open deletion requests |
| 4 | Dependency / CVE skim | Critical npm advisories on web app |
| 5 | Customer success | Open Sev tickets, CSAT/feedback themes |

---

## Incident response (abbreviated)

1. Detect (health/ready/user report).  
2. Contain (feature freeze / disable checkout / rotate secrets as needed).  
3. Communicate (`/status` maintenance or incident entry + support email).  
4. Eradicate / recover (rollback, restore per BCP).  
5. Post-mortem (internal notes; update Risk Register if material).  

Severity definitions: [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md).

---

## Backup & restore

Follow [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md) and `docs/RECOVERY.md`. Verify restore path quarterly — do not claim untested RTO/RPO.

---

## Support & revenue

- Support: [SUPPORT_OPERATIONS.md](./SUPPORT_OPERATIONS.md) · Help Center · tickets.  
- Refunds: Paddle MoR + `/refund`.  
- Revenue: Paddle transactions + internal billing ledger — never invent ARR.

---

## Security review (monthly minimum)

- [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md)  
- Public `/security` accuracy (Implemented vs Roadmap)  
- No premature SOC/ISO badges on marketing

---

## Compliance docs index

- [docs/compliance/LEGAL_COMPLIANCE.md](../compliance/LEGAL_COMPLIANCE.md)  
- [docs/compliance/SECURITY_OVERVIEW.md](../compliance/SECURITY_OVERVIEW.md)  
- [docs/compliance/DATA_PRIVACY.md](../compliance/DATA_PRIVACY.md)  
- [docs/compliance/COOKIE_MANAGEMENT.md](../compliance/COOKIE_MANAGEMENT.md)  
- [docs/compliance/USER_DATA_REQUESTS.md](../compliance/USER_DATA_REQUESTS.md)  
- [docs/compliance/SYSTEM_STATUS.md](../compliance/SYSTEM_STATUS.md)
