# RTAS Studio AI — CRM Workflow

**Classification:** Sales operations / RevOps  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 4  
**Cross-links:** [`Sales-Playbook.md`](./Sales-Playbook.md) · [`Enterprise-Sales-Process.md`](./Enterprise-Sales-Process.md) · [`Sales-KPI.md`](./Sales-KPI.md) · [`business/sales/ICP.md`](../../../business/sales/ICP.md)

---

## 1. CRM purpose

The CRM is the **single source of truth** for pipeline, follow-ups, forecasting, and sales KPIs. At lean stage, a lightweight CRM (HubSpot free, Pipedrive, Notion+Sheets, or equivalent) is acceptable—**process discipline matters more than tool brand**.

**Rules**

- No deal exists if it is not in CRM  
- Every enterprise/assisted opportunity has a stage, next step, and date  
- Self-serve Standard/Premium may be summarized as aggregated MRR with cohort notes; high-touch deals are fully staged  
- Never store card data in CRM; Paddle is MoR  

---

## 2. Lead sources (taxonomy)

| Source code | Description | Typical motion |
|-------------|-------------|----------------|
| `web_contact` | contact@ / info@ / form | Inbound |
| `web_signup` | Product signup | PLG |
| `support_upgrade` | support@ conversation → sales | Assist |
| `outbound_email` | Cold/warm email | Outbound |
| `outbound_linkedin` | LinkedIn sequence | Outbound |
| `partner_referral` | Agency/partner intro | Partner |
| `rtas_network` | RTAS Digital Marketing Company network | Warm |
| `event` | Conference / meetup | Outbound/inbound hybrid |
| `investor_intro` | VC/angel/strategic intro | Warm |
| `content_seo` | Organic content conversion | Inbound |
| `other` | Must add note | — |

Campaign UTM fields recommended: `utm_source`, `utm_medium`, `utm_campaign`.

---

## 3. Lead scoring

### 3.1 Fit score (0–40)

| Signal | Points |
|--------|--------|
| Agency / marketing company / enterprise marketing | +15 |
| Creator / freelancer with commercial clients | +8 |
| Startup growth team | +10 |
| Production boutique / media house | +10 |
| Explicit unauthorized-use request | **−40 (auto-DQ)** |
| Requires day-one SSO/SOC2 with no pilot | −10 |
| English-web commercial buyer | +5 |

### 3.2 Intent score (0–40)

| Signal | Points |
|--------|--------|
| Requested demo / enterprise pricing | +15 |
| Started Tester | +10 |
| Asked Standard/Premium comparison | +8 |
| Named campaign deadline ≤60 days | +10 |
| Multi-seat / team language | +8 |
| Ghosted after two touches | −10 |

### 3.3 Authority score (0–20)

| Signal | Points |
|--------|--------|
| Economic buyer engaged | +12 |
| Champion only | +6 |
| Unknown role | +2 |

**Total:** Fit + Intent + Authority = **0–100**

| Band | Label | Action |
|------|-------|--------|
| 70–100 | Hot | Founder response priority; demo ≤3 days |
| 45–69 | Warm | Standard cadence |
| 25–44 | Cool | Nurture content |
| <25 or DQ flag | Unqualified | Close or park; no forecast |

Recalculate on stage changes and major email events.

---

## 4. Pipeline stages (CRM fields)

Align assisted/enterprise deals to:

1. Lead  
2. Qualify  
3. Discovery  
4. Demo  
5. Technical / Trust review  
6. Proposal  
7. Negotiation  
8. Closed-Won  
9. Onboarding  
10. Adoption  
11. Expansion  
12. Renewal  

Self-serve may use a simplified funnel: `Signup → Tester → Paid → Churned/Active`.

**Required fields per opportunity**

| Field | Required |
|-------|----------|
| Account name | Yes |
| Primary contact | Yes |
| Source | Yes |
| Segment (ICP persona) | Yes |
| Stage | Yes |
| Amount (MRR or pilot value) | Yes if past Qualify |
| Close date | Yes if past Demo |
| Next step + next step date | Yes |
| Plan interest (Tester/Standard/Premium/Multi) | Yes |
| Authorized-use confirmed (Y/N/NA) | Yes past Qualify |
| MoR/checkout risk flag | Yes |
| Loss reason | If Closed-Lost |

---

## 5. Follow-up rules

| Situation | Cadence |
|-----------|---------|
| New inbound Hot | Same day; if missed, next business morning |
| Post-demo no reply | Day 2, Day 5, Day 10, then nurture |
| Proposal sent | Day 3 check-in; Day 7; Day 14 decision ask |
| Negotiation idle >7 days | Reconfirm blockers; offer call |
| Onboarding | Day 0, 3, 7, 14 touches |
| Renewal | T−60, T−45, T−30, T−14 |

**Max attempts before nurture:** 4 substantive touches without engagement.

Every follow-up must advance value (answer, asset, or decision)—not “just bumping.”

---

## 6. Email automation (lean)

Automate only what stays accurate if MoR status changes.

### 6.1 Allowed automations

| Sequence | Trigger | Content focus |
|----------|---------|---------------|
| Welcome / activate | Signup | First generate + credit explanation |
| Tester expiry nudge | Day 3–4 of Tester | Upgrade to Standard before window ends |
| Paid welcome | First Standard/Premium | Support path + credit planning |
| Win-back | Churn / lapse | Honest value + Tester re-entry if appropriate |
| Nurture monthly | Cool leads | Use-case education; trust posture; no fake metrics |

### 6.2 Human-only (do not fully automate)

- Enterprise proposals  
- Security/legal answers  
- Discount commitments  
- Partnership terms  
- Anything implying checkout is live if it is not  

### 6.3 From-addresses

Use @rtasstudio.com properties: contact@, info@, support@ as role-appropriate. Keep auth@ for authentication-related mail only.

---

## 7. Pipeline hygiene

**Weekly hygiene checklist**

- [ ] No opportunity without next step date  
- [ ] Stale deals (>14 days silence) updated or Closed-Lost/Nurture  
- [ ] Amounts match published economics or approved custom pilot math  
- [ ] DQ unauthorized-use leads removed from forecast  
- [ ] MoR blockers tagged on affected deals  

**Definition of pipeline coverage:** Sum of open opportunity amounts in stages Discovery→Negotiation, weighted (see forecasting).

---

## 8. Forecasting model

### 8.1 Stage weights (planning defaults)

| Stage | Weight |
|-------|--------|
| Lead / Qualify | 5–10% (often exclude from commit) |
| Discovery | 20% |
| Demo | 35% |
| Technical / Trust | 45% |
| Proposal | 55% |
| Negotiation | 70% |
| Closed-Won | 100% |

**Commit forecast** = sum(amount × weight) for deals with close date in period + existing MRR  
**Best case** = commit + lower-stage upside  
**Pipeline coverage target (assisted):** ≥3× next-quarter new-MRR goal once goals exist  

### 8.2 Self-serve overlay

Add expected self-serve new MRR from trailing conversion rates (Tester→Paid, signup→Paid). Until 30+ paying observations exist, label self-serve forecast **ESTIMATE**.

### 8.3 MoR adjustment

If checkout is impaired, apply a **collection risk haircut** (e.g., 30–100%) to near-term new MRR forecasts and state it explicitly in weekly notes.

---

## 9. KPIs logged from CRM

See full formulas in [`Sales-KPI.md`](./Sales-KPI.md). CRM must support extraction of:

- Stage conversion rates  
- Sales cycle length (Lead→Closed-Won)  
- Win rate  
- Pipeline value and coverage  
- Source → Closed-Won attribution  
- Renewal rate / churn reasons  
- Activity metrics (demos booked, proposals sent)

---

## 10. Roles and permissions (lean)

| Role | Access |
|------|--------|
| Founder | Full |
| AE / sales | Own + team pipeline |
| Support | Contact history; no arbitrary deal amount edits |
| Marketing | Lead sources/campaigns; no closed-won edits |

---

## 11. Implementation starter (week one)

1. Choose CRM tool and create stage pipeline matching this doc  
2. Import ICP segments as dropdown  
3. Add source taxonomy  
4. Create views: Hot leads · Enterprise process · Renewals ≤60d · Stale deals  
5. Schedule weekly 30-minute pipeline review  
6. Connect email logging if available  
7. Document MoR status as a pinned CRM note until resolved  

---

*CRM workflow quality = forecast quality. If it is not logged, it is not managed.*
