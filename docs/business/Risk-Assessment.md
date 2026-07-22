# RTAS Studio AI — Risk Assessment

**Classification:** Confidential — Board / M&A / Risk committee  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (Pakistan)  
**Phase:** 11 · Sprint 3  

**Scales**

| Scale | Probability | Impact |
|-------|-------------|--------|
| 1 | Rare | Negligible |
| 2 | Unlikely | Minor |
| 3 | Possible | Moderate |
| 4 | Likely | Major |
| 5 | Almost certain | Severe / existential |

**Score** = Probability × Impact (1–25).  
**Bands:** 1–6 Low · 7–12 Medium · 13–19 High · 20–25 Critical  

---

## Risk matrix (summary)

| ID | Risk | Prob. | Impact | Score | Band |
|----|------|------:|-------:|------:|------|
| R01 | Paddle MoR / checkout delayed or re-rejected | 4 | 5 | 20 | Critical |
| R02 | Inference COGS inflate; margins collapse | 3 | 4 | 12 | Medium |
| R03 | Key-person / single-operator dependency | 4 | 4 | 16 | High |
| R04 | Category competition & price pressure | 4 | 3 | 12 | Medium |
| R05 | AUP / Trust & Safety compliance drift | 2 | 5 | 10 | Medium |
| R06 | Fal or model-provider outage / terms change | 3 | 4 | 12 | Medium |
| R07 | Security incident (account/data breach) | 2 | 5 | 10 | Medium |
| R08 | Weak conversion / high churn (no product-market fit proof) | 3 | 4 | 12 | Medium |
| R09 | IP chain-of-title incomplete at sale | 3 | 4 | 12 | Medium |
| R10 | Domain / DNS / email deliverability failure | 2 | 4 | 8 | Medium |
| R11 | Legal claim (content misuse by end user) | 3 | 4 | 12 | Medium |
| R12 | Talent / contractor continuity gap | 3 | 3 | 9 | Medium |
| R13 | FX / cross-border payment friction | 2 | 3 | 6 | Low |
| R14 | Overstated traction in external materials | 2 | 5 | 10 | Medium |
| R15 | DR failure / data loss | 2 | 5 | 10 | Medium |
| R16 | Enterprise sales expectations exceed readiness | 3 | 3 | 9 | Medium |
| R17 | Cloud vendor lock-in cost shock | 2 | 3 | 6 | Low |
| R18 | Regulatory change (AI / deepfake laws) | 3 | 4 | 12 | Medium |

---

## Detailed risks & mitigations

### R01 — Paddle MoR / checkout delayed or re-rejected
**Score: 20 Critical**

| | |
|--|--|
| Description | Live paid conversion blocked; valuation and GTM stall |
| Indicators | Vendor dashboard “checkout not enabled”; failed live purchases |
| Mitigation | Maintain AUP-safe Identity Preservation positioning; complete vendor onboarding; keep compliance docs current; escalate with evidence pack (`PADDLE_COMPLIANCE_REPORT.md`); consider contingency MoR only if Paddle path definitively fails |
| Owner | Operator / commercial lead |
| Residual risk | Medium if approved; Critical until live |

### R02 — Inference COGS inflate
**Score: 12 Medium**

| | |
|--|--|
| Description | Fal pricing, retries, or 4K mix destroy contribution margin |
| Mitigation | Tier routing; monitor $ per second; credit pricing reviews; cache/reuse where product-appropriate; Premium COGS transparency |
| Owner | Product + ops |

### R03 — Key-person dependency
**Score: 16 High**

| | |
|--|--|
| Description | Bus-factor = 1 for secrets, DNS, releases, vendor relationships |
| Mitigation | Access matrix; documented runbooks; second trusted admin; escrow instructions for acquisition; contractor coverage |
| Owner | Operator |

### R04 — Category competition
**Score: 12 Medium**

| | |
|--|--|
| Description | Incumbents outspend on brand/models; RTAS share stays niche |
| Mitigation | Own packaging/ICP; agency motion; trust narrative; avoid feature arms race without margin math |
| Owner | GTM |

### R05 — Compliance drift
**Score: 10 Medium**

| | |
|--|--|
| Description | Marketing or Studio copy reintroduces deepfake/face-swap implications |
| Mitigation | Legal suite as source of truth; review checklist for launches; Trust & Safety ownership |
| Owner | Product + legal posture owner |

### R06 — Provider outage / terms change
**Score: 12 Medium**

| | |
|--|--|
| Description | Fal downtime or contract change halts generation |
| Mitigation | Status monitoring; customer comms templates; evaluate secondary provider longer-term; wallet alerts |
| Owner | Engineering ops |

### R07 — Security incident
**Score: 10 Medium**

| | |
|--|--|
| Description | Credential leak, account takeover, or data exposure |
| Mitigation | Follow `docs/SECURITY.md`; rotate secrets; fail-closed webhooks; rate limits; incident response plan in VDR |
| Owner | Technical owner |

### R08 — Weak conversion / churn
**Score: 12 Medium**

| | |
|--|--|
| Description | Signups without retained paid seats; illustrative projections miss |
| Mitigation | Measure Tester→Standard; improve onboarding; support quality; honest ICP focus |
| Owner | Product + GTM |

### R09 — IP chain-of-title gap
**Score: 12 Medium**

| | |
|--|--|
| Description | Acquirer counsel blocks close without assignments |
| Mitigation | Execute contributor IP assignments; SBOM; trademark posture clarity; VDR folder 12 |
| Owner | Operator + counsel |

### R10 — Domain / email failure
**Score: 8 Medium**

| | |
|--|--|
| Description | DNS misconfig, expired domain, or spam folding kills auth/commerce |
| Mitigation | DNS docs; registrar locks; SPF/DKIM/DMARC monitoring; renewal calendar |
| Owner | Ops |

### R11 — End-user misuse claim
**Score: 12 Medium**

| | |
|--|--|
| Description | User generates prohibited content; platform liability narrative |
| Mitigation | Clear prohibited uses; Trust & Safety; abuse reporting path; MoR alignment; moderation capacity plan |
| Owner | Trust & Safety owner |

### R12 — Talent continuity
**Score: 9 Medium**

| | |
|--|--|
| Description | Contractors depart; delivery slows |
| Mitigation | Written agreements; knowledge docs; prioritized backlog |
| Owner | Operator |

### R13 — FX / cross-border friction
**Score: 6 Low**

| | |
|--|--|
| Description | Operator costs in PKR vs USD revenue; payout delays |
| Mitigation | MoR settlements discipline; cash buffer; accounting hygiene |
| Owner | Finance owner |

### R14 — Overstated traction
**Score: 10 Medium**

| | |
|--|--|
| Description | Deck claims invent ARR/users → trust destruction in diligence |
| Mitigation | Sprint 1–3 honesty rules; separate VERIFIED vs ILLUSTRATIVE; counsel review of CIM |
| Owner | Board / operator |

### R15 — DR / data loss
**Score: 10 Medium**

| | |
|--|--|
| Description | Backup failure loses customer assets or DB |
| Mitigation | Backup docs → **tested restores**; RTO/RPO; provider snapshot verification |
| Owner | Technical ops |

### R16 — Enterprise expectation mismatch
**Score: 9 Medium**

| | |
|--|--|
| Description | Selling SSO/SOC2 before ready damages brand |
| Mitigation | Position enterprise as developing ICP; use pilot language; Sprint 2 enterprise templates with honesty |
| Owner | Sales |

### R17 — Cloud cost shock
**Score: 6 Low**

| | |
|--|--|
| Description | Vercel/Supabase bills spike with traffic |
| Mitigation | Budgets/alerts; architecture reviews; caching |
| Owner | Ops |

### R18 — AI regulatory change
**Score: 12 Medium**

| | |
|--|--|
| Description | New deepfake/labeling laws raise compliance cost |
| Mitigation | Already aligned to authorized-use narrative; watch major markets; labeling features if required |
| Owner | Legal posture + product |

---

## Heat map (visual)

```text
Impact →     1        2        3        4        5
Prob ↓
5
4                      R04            R03       R01
3               R12/R16     R02/R06/R08/R09/R11/R18
2                      R13/R17        R10       R05/R07/R14/R15
1
```

---

## Top 5 residual risks after mitigation (board focus)

1. **R01 MoR live status** — until checkout is verified live.  
2. **R03 Key-person** — until access redundancy exists.  
3. **R08 Traction proof** — until cohort metrics exist.  
4. **R02 COGS** — until Fal unit economics are instrumented.  
5. **R09 IP assignments** — until VDR legal pack complete.

---

## Risk governance recommendations

| Cadence | Action |
|---------|--------|
| Weekly | MoR status, Fal balance, uptime, support queue |
| Monthly | Risk register review; margin vs plan |
| Quarterly | DR restore drill; access audit; policy drift review |
| Deal process | Fresh risk letter to buyers; update scores |

---

## Overall risk posture

For an early-stage AI video SaaS with completed v1.0 engineering, residual risk is **High but manageable**, dominated by **commercial enablement (MoR)** and **operator concentration**, not by absence of a product. Risk score improves materially when R01 and R03 move from High/Critical to Medium.

*Companion: `Acquisition-Readiness-Checklist.md`, `Technical-Due-Diligence.md`, `Exit-Strategy.md`.*
