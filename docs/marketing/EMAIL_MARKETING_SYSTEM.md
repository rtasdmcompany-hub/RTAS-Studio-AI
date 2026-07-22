# RTAS Studio AI — Email Marketing System

**Classification:** Marketing / lifecycle email  
**Phase:** 12 · Sprint 5  
**Integrity:** Templates and triggers only. Do not invent open rates, list sizes, or revenue attribution.

Cross-links: [`MARKETING_MASTER_PLAN.md`](MARKETING_MASTER_PLAN.md) · transactional email docs under `/docs` · Help contact pages

---

## 1. Principles

1. **Transactional first** — auth, billing, video-ready, password reset must work before nurture scale.  
2. **Honest offers** — Tester $5 entry; no “free trial” subject lines.  
3. **Canonical plan names** in every commercial email.  
4. **Consent & privacy** — align with Privacy Policy / Cookies; unsubscribe on marketing sends.  
5. From-domain: prefer `rtasstudio.com` aliases (`contact@`, `support@`, product noreply as configured).

---

## 2. Lifecycle map

```text
Signup → Welcome → Activation (first render) → Education
    → Product updates → Renewal / usage → Upgrade
    → Retention / win-back → Re-engagement (lapsed)
```

---

## 3. Programs

### A. Welcome
| Field | Spec |
|-------|------|
| Trigger | Email verified / account created |
| Goal | Orient to Studio + pricing truth |
| Content | What RTAS is; 1 credit = 1 second; Tester vs Standard vs Premium; links to How-to-use, Pricing |
| CTA | Open Studio · View pricing |

### B. Activation
| Field | Spec |
|-------|------|
| Trigger | Signup + N days without successful generation **or** zero credits after signup |
| Goal | First successful render |
| Content | How-to steps; Tester as low-risk proof; common failures → troubleshooting |
| CTA | Start Tester · How to use |

### C. Education
| Field | Spec |
|-------|------|
| Trigger | After first success; drip 3–5 emails |
| Goal | Habit + trust |
| Content | Credits math for 15s ads; Identity Preservation authorized-only; Standard vs Premium; commercial rights |
| CTA | Pricing · Features · Trust & Safety |

### D. Updates
| Field | Spec |
|-------|------|
| Trigger | Changelog / meaningful ship |
| Goal | Retention via product progress |
| Content | What changed; how it helps creators; link `/help/changelog` |
| CTA | Open Studio |

### E. Renewal
| Field | Spec |
|-------|------|
| Trigger | Approaching period end (Standard/Premium); Tester window end |
| Goal | Reduce involuntary churn / clarify next step |
| Content | Days left; what happens to credits; upgrade path Tester → Standard |
| CTA | Manage plans · Upgrade |

### F. Upgrade
| Field | Spec |
|-------|------|
| Trigger | Hit Tester cap; HD/commercial need; 4K intent signals |
| Goal | Standard or Premium conversion |
| Content | Side-by-side plan facts only |
| CTA | Go Standard · Go Premium 4K |

### G. Retention
| Field | Spec |
|-------|------|
| Trigger | Unused credits mid-cycle; support ticket resolved |
| Goal | Keep plan useful |
| Content | Prompt ideas; Discord; How-to refresh |
| CTA | Open Studio · Join Discord |

### H. Re-engagement
| Field | Spec |
|-------|------|
| Trigger | No login N days after paid period; canceled |
| Goal | Win-back without spam |
| Content | What’s new; honest invite back; unsubscribe respect |
| CTA | Pricing · Contact support |

---

## 4. Operational checklist

- [ ] ESP / Resend (or current provider) domains verified  
- [ ] Suppression list for bounces/complaints  
- [ ] Marketing vs transactional streams separated  
- [ ] Footer: company identity, privacy link, unsubscribe (marketing)  
- [ ] QA: every template uses Tester/Standard/Premium 4K correctly  
- [ ] No fabricated social proof blocks in email HTML  

---

## 5. Metrics (formulas only)

| Metric | Formula |
|--------|---------|
| Delivery rate | `delivered / sent` |
| Open rate | `unique_opens / delivered` (privacy-aware) |
| CTR | `unique_clicks / delivered` |
| Welcome → Tester | `tester_checkouts_attributed / welcome_delivered` |
| Unsubscribe rate | `unsubs / delivered` |
| Complaint rate | `complaints / delivered` |

Leave measured values blank until ESP exports exist. See [`MARKETING_KPI_FRAMEWORK.md`](MARKETING_KPI_FRAMEWORK.md).
