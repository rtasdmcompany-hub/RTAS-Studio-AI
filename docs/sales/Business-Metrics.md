# RTAS Studio AI — Business Metrics Handbook

**Purpose:** Define investor- and operator-grade SaaS metrics with formulas.  
**Fact policy:** Formulas are universal. **Worked numbers are Hypothetical** unless marked Verified.  
**Verified commercial anchors:** Tester $5 / 30s / 5 days; Standard $89/mo / 2000s; Premium $249/mo / 2000s; 1 credit = 1 second.

RTAS does **not** publish invented live MRR/ARR in this kit.

---

## 1. MRR — Monthly Recurring Revenue

**Definition:** Sum of normalized monthly subscription revenue from active recurring accounts.

\[
MRR = \sum_i Price_i^{\text{(monthly normalized)}}
\]

**Include:** Standard and Premium active subscriptions.  
**Exclude / careful:** One-time Tester ($5) is **not** classic MRR (treat as non-recurring or separately as activation revenue).

### Hypothetical example

| Plan | Seats | Price | Contribution |
|------|------:|------:|-------------:|
| Standard | 40 | $89 | $3,560 |
| Premium | 10 | $249 | $2,490 |
| **MRR** | | | **$6,050** |

*Label: Hypothetical — not RTAS reported revenue.*

---

## 2. ARR — Annual Recurring Revenue

\[
ARR = MRR \times 12
\]

**Hypothetical:** \(6050 \times 12 = \$72,600\) ARR.

For annual prepay (if introduced later): recognize in MRR as monthly equivalent per accounting policy.

---

## 3. CAC — Customer Acquisition Cost

\[
CAC = \frac{\text{Sales \& Marketing spend in period}}{\text{New paying customers in period}}
\]

### Hypothetical example

- S&M spend (month): $12,000  
- New paying customers: 30  
- \(CAC = 12000 / 30 = \$400\)

*Hypothetical.*

---

## 4. LTV — Customer Lifetime Value

**Simple contribution LTV:**

\[
LTV = ARPU_{\text{month}} \times Gross\ Margin\% \times Customer\ Lifetime_{\text{months}}
\]

**Lifetime months** from churn:

\[
Lifetime_{\text{months}} \approx \frac{1}{Monthly\ Logo\ Churn}
\]

### Hypothetical example

- Blended ARPU: $120 / mo  
- Gross margin: 70%  
- Monthly churn: 4% → lifetime ≈ 25 months  
- \(LTV = 120 \times 0.70 \times 25 = \$2,100\)

**LTV:CAC** = \(2100 / 400 = 5.25\times\) (healthy SaaS heuristic often cites >3×; context matters).

*All Hypothetical.*

---

## 5. Gross Margin

\[
Gross\ Margin\% = \frac{Revenue - COGS}{Revenue}
\]

**AI video COGS typically include:** Fal/GPU inference, bandwidth, incremental storage, MoR fees attributable to COGS policy.

### Hypothetical per-second COGS bridge

| Item | Assumption |
|------|------------|
| GPU cost / second | $0.03 |
| Other variable / second | $0.005 |
| **COGS / second** | **$0.035** |

Standard plan revenue per included second (if fully consumed): \(89 / 2000 = \$0.0445\)/s → rough contribution before fixed opex.

*Hypothetical COGS — replace with live Fal invoices.*

---

## 6. Payback Period (CAC)

\[
Payback_{\text{months}} = \frac{CAC}{ARPU \times Gross\ Margin\%}
\]

**Hypothetical:** \(400 / (120 \times 0.70) \approx 4.8\) months.

Target heuristics vary; many SaaS teams aim for <12 months payback.

---

## 7. Burn Multiple

\[
Burn\ Multiple = \frac{Net\ Burn}{Net\ New\ ARR}
\]

Where net burn is cash decrease from operations in the period, and net new ARR is ARR added net of churn (period-normalized).

| Burn Multiple | Rough read |
|---------------|------------|
| <1× | Efficient |
| 1×–2× | Acceptable early |
| >3× | Expensive growth |

### Hypothetical

- Net burn / quarter: $90,000  
- Net new ARR / quarter: $60,000  
- Burn Multiple = 1.5×

---

## 8. Rule of 40

\[
Rule\ of\ 40 = Growth\%_{\text{YoY revenue}} + Profit\ Margin\%
\]

Often use revenue growth % + free cash flow margin % (or EBITDA margin—be consistent).

**Heuristic:** ≥ 40 is “healthy” for many growth SaaS narratives.

### Hypothetical

- YoY growth: 80%  
- FCF margin: −20%  
- Score: 60 (passes Rule of 40 on growth strength)

*Hypothetical.*

---

## 9. NRR — Net Revenue Retention

\[
NRR\% = \frac{Starting\ ARR + Expansions - Contractions - Churned}{Starting\ ARR} \times 100
\]

(Cohort of existing customers only; exclude brand-new logos from numerator expansions carefully per definition.)

| NRR | Read |
|-----|------|
| <100% | Shrinkage |
| 100–120% | Solid |
| >120% | Excellent expansion |

### Hypothetical

- Starting ARR: $50,000  
- Expansions: $8,000  
- Contractions: $2,000  
- Churned: $3,000  
- Ending from cohort: $53,000  
- NRR = 106%

---

## 10. Enterprise Sales Cycle

**Definition:** Days from qualified opportunity creation to closed-won (or closed-lost).

\[
Sales\ Cycle_{\text{days}} = Close\ Date - Opportunity\ Created\ Date
\]

**Median** is preferred over mean when outliers exist.

### Hypothetical enterprise motion

| Stage | Typical duration (Estimate) |
|-------|----------------------------|
| Discovery + security packet | 1–3 weeks |
| Pilot (Tester → Standard) | 1–4 weeks |
| Procurement / MoR invoicing | 2–8 weeks |
| **Total cycle** | **~6–15 weeks** |

Self-serve Standard checkout can be **same day** once MoR live paths are active—different motion than enterprise paper.

---

## 11. Blended ARPU helper (RTAS plans)

\[
ARPU = \frac{MRR}{Paying\ Recurring\ Accounts}
\]

**Hypothetical mix:** 80% Standard / 20% Premium →  
\(ARPU = 0.8\times89 + 0.2\times249 = \$121\)

---

## 12. Metric operating cadence (recommended)

| Cadence | Metrics |
|---------|---------|
| Weekly | New subs, churn logos, GPU $ / second, generation success rate |
| Monthly | MRR, ARPU, CAC, payback, gross margin |
| Quarterly | ARR, NRR, Burn Multiple, Rule of 40 components |

---

## Related

[Enterprise-ROI-Calculator.md](./Enterprise-ROI-Calculator.md) · [Investor-FAQ.md](./Investor-FAQ.md) · [Pitch-Deck.md](./Pitch-Deck.md)
