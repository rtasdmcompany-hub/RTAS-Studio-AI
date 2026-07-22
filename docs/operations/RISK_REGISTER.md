# Risk Register — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Method:** Qualitative probability × impact (1–5); score = P × I  

**Related:** [VENDOR_MANAGEMENT.md](./VENDOR_MANAGEMENT.md) · [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md) · [COMPLIANCE_REGISTER.md](./COMPLIANCE_REGISTER.md) · [business/company/SWOT.md](../../business/company/SWOT.md) · [business/roadmap/BUSINESS_ROADMAP.md](../../business/roadmap/BUSINESS_ROADMAP.md)

---

## Scoring guide

| Score | Probability | Impact |
|------:|-------------|--------|
| 1 | Rare | Negligible |
| 2 | Unlikely | Limited |
| 3 | Possible | Moderate |
| 4 | Likely | Severe |
| 5 | Almost certain | Critical (business-stopping) |

| Band | P×I | Treatment |
|------|-----|-----------|
| Low | 1–6 | Monitor |
| Medium | 7–12 | Mitigate / schedule |
| High | 13–19 | Priority mitigation |
| Critical | 20–25 | Immediate executive attention |

**Status values:** Open · Mitigating · Accepted · Closed  

---

## Risk register

| ID | Risk | Category | P | I | Score | Owner | Mitigation (current) | Target date | Status |
|----|------|----------|--:|--:|------:|-------|----------------------|-------------|--------|
| R-01 | Paddle MoR checkout/domain not fully activated or re-rejected on AUP | Commercial / Compliance | 4 | 5 | **20** | Ops Owner | Legal v1.1 + Trust & Safety/AI Policy live; marketing discipline; track Paddle review honestly | Ongoing (commercial gate) | **Mitigating** |
| R-02 | Fal.ai outage or credit exhaustion blocks generation | Operations / Vendor | 3 | 5 | **15** | Ops Owner | Balance monitoring; optional Replicate fallback; degrade messaging | Weekly ops | **Mitigating** |
| R-03 | Single-operator key-person dependency | Organizational | 4 | 4 | **16** | Ops Owner | Written SOPs (this Sprint 6 pack); password manager; document vendor access | Q4 2026 playbook completeness | **Mitigating** |
| R-04 | Production secrets leaked (git, chat, screenshot) | Security | 2 | 5 | **10** | Ops Owner | Gitignore; Vercel env; rotation SOP; fail closed | Continuous | **Mitigating** |
| R-05 | Bad production deploy causes site outage | Change | 3 | 4 | **12** | Ops Owner | Release checklist; Vercel promote rollback; smoke tests | Continuous | **Mitigating** |
| R-06 | Database loss / failed restore | Continuity | 2 | 5 | **10** | Ops Owner | Supabase backups/PITR; restore drills; continuity plan | Quarterly drill | **Mitigating** |
| R-07 | DNS misconfiguration breaks domain, SSL, or email auth | Infrastructure | 3 | 4 | **12** | Ops Owner | DNS documentation; Cloudflare change control; post-change verify | Continuous | **Mitigating** |
| R-08 | Webhook failure causes credit/billing desync | Payments | 3 | 4 | **12** | Ops Owner | HMAC verify; monitoring; manual reconciliation SOP | Monthly review when live | **Mitigating** |
| R-09 | Generative AUP abuse (unauthorized likeness / deepfake attempts) damages MoR or brand | Trust & Safety | 3 | 5 | **15** | Ops Owner | Public policies; support refusal SOP; account restriction when available | Continuous | **Mitigating** |
| R-10 | Email deliverability failure (verification, resets, ready notices) | Operations | 3 | 3 | **9** | Ops Owner | Resend domain auth; Forward Email checks; SOP-09 | Monthly | **Mitigating** |
| R-11 | Google OAuth misconfiguration locks social login | Auth | 2 | 3 | **6** | Ops Owner | Console redirect hygiene; credentials path remains | Monthly smoke | **Mitigating** |
| R-12 | Cost overrun on Fal / Vercel without matching revenue | Finance | 3 | 4 | **12** | Ops Owner | Usage reviews; pricing model; kill-switches in GTM docs | Monthly | **Mitigating** |
| R-13 | Overclaiming enterprise certifications in sales/support | Compliance / Reputation | 2 | 4 | **8** | Ops Owner | Governance docs forbid ISO/SOC2/GDPR cert claims; questionnaire script | Continuous | **Mitigating** |
| R-14 | Dependency CVE (e.g. Next.js advisory path) | Security / Supply chain | 3 | 3 | **9** | Ops Owner | npm audit cadence; upgrade planning | Quarterly | **Mitigating** |
| R-15 | Registrar (Hostinger history) access loss or expiry | Domain | 2 | 4 | **8** | Ops Owner | Confirm registrar login; renewal calendar; Cloudflare DNS independence where applicable | Semi-annual | **Open** |
| R-16 | No contractual customer SLA → enterprise deal friction | GTM | 4 | 3 | **12** | Ops Owner | Honest enterprise docs; future SLA/DPA as Goal | 2026–2027 packaging | **Accepted** (stage-appropriate) |
| R-17 | Multi-instance rate-limit weakness without Redis/KV | Security | 3 | 3 | **9** | Ops Owner | KV when linked; monitor abuse | When scaling | **Open** |
| R-18 | Incomplete CRM/ticketing → missed support RTAs | Support | 4 | 2 | **8** | Ops Owner | Mailbox discipline; Support Ops RTAs; CRM Goal | Q4 2026 | **Open** |
| R-19 | Vendor concentration (Vercel+Supabase+Fal+Paddle) | Strategic | 3 | 4 | **12** | Ops Owner | Continuity playbooks; no false dual-active claims | Annual strategy | **Accepted** (with mitigations) |
| R-20 | Legal version drift vs live site | Compliance | 2 | 3 | **6** | Ops Owner | Compliance register; legal sign-off process | Quarterly | **Mitigating** |

---

## Top risks (attention order)

1. **R-01** — MoR checkout/domain gate (Critical band)  
2. **R-03** — Key-person dependency (High)  
3. **R-02 / R-09** — Generation vendor & AUP abuse (High)  
4. **R-05 / R-07 / R-08** — Deploy, DNS, webhook integrity (Medium–High)  

---

## Review rules

- Update after every SEV1/SEV2.  
- Full pass monthly (status + scores).  
- Do not close R-01 until Paddle checkout is reliably live and observed.  
- Do not mark certification risks “Closed” by inventing certificates.

**Owner:** Ops Owner · **Phase 11 Sprint 6**
