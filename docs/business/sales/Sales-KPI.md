# RTAS Studio AI — Sales KPIs

**Classification:** Sales operations / Finance-aligned metrics  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 4  
**Cross-links:** [`CRM-Workflow.md`](./CRM-Workflow.md) · [`Go-To-Market-Strategy.md`](./Go-To-Market-Strategy.md) · [`business/roadmap/BUSINESS_ROADMAP.md`](../../../business/roadmap/BUSINESS_ROADMAP.md) · [`business/finance/README.md`](../../../business/finance/README.md)

---

## How to use this document

All formulas below are **definitions for measurement**. They do **not** invent historical RTAS revenue, users, or conversion rates. Until finance publishes verified figures, report KPIs as **measured** (with date range) or **not yet instrumented**.

**Pricing anchors (verified):** Tester $5 / 30s / 5 days · Standard $89/mo / 2000s · Premium $249/mo / 2000s · 1 credit = 1 second · Paddle MoR (checkout may be pending—flag collection gaps in KPI commentary).

---

## 1. MRR — Monthly Recurring Revenue

**Definition:** Sum of normalized monthly subscription revenue from active Standard and Premium (and future recurring enterprise seats) at period end.

```text
MRR = Σ (monthly_price_of_active_subscription_i)
```

**Rules**

- Standard seat contributes **$89** per active month  
- Premium seat contributes **$249** per active month  
- Tester ($5 one-time) is **not** MRR; track as **Non-recurring revenue (NRR one-time)**  
- Multi-seat: sum seat MRR  
- Discounts: use **net** collected/authorized amount  
- Refunds in-month: reduce MRR or show contra line consistently  

**Enterprise pilots:** If billed monthly recurring, include in MRR. If one-time pilot fee, classify separately until converted to recurring.

**MoR gap note:** Bookings ≠ collections if checkout fails—report **Collected MRR** vs **Contracted MRR** when they diverge.

---

## 2. ARR — Annual Recurring Revenue

```text
ARR = MRR × 12
```

Use period-end MRR. For annual prepay (future), still recognize ARR as 12× monthly equivalent of the subscription, per finance policy once defined.

Do not annualize one-time Tester fees.

---

## 3. CAC — Customer Acquisition Cost

```text
CAC = Sales_and_Marketing_Costs_in_Period / New_Customers_Acquired_in_Period
```

**Include (fully loaded when possible):** paid ads, agency fees, marketing tools, sales salaries/contractor time allocated to acquisition, event spend attributable to acquisition, outsourced SDR.

**Exclude:** pure R&D, unrelated corporate overhead (or allocate consistently).

**Variants**

| Variant | Formula focus |
|---------|----------------|
| **Blended CAC** | All new paying customers |
| **Paid CAC** | Costs of paid channels / customers from paid |
| **Assisted CAC** | Outbound+sales cost / assisted Closed-Won |
| **Organic CAC** | Often near-zero cash; still track time cost qualitatively |

**New customer:** First paid Standard/Premium (or paid enterprise seat). Tester-only buyers are **not** paying customers for CAC denominator unless finance defines otherwise—prefer **Tester buyers** as a separate funnel metric.

---

## 4. LTV — Customer Lifetime Value

**Simple gross LTV (early-stage default):**

```text
LTV_gross = ARPU_monthly × Gross_Margin × Average_Customer_Lifetime_months
```

Where:

```text
ARPU_monthly = MRR / Active_Paying_Customers
Average_Customer_Lifetime_months ≈ 1 / Monthly_Logo_Churn_Rate
```

**Example structure (illustrative only, not RTAS actuals):**  
If ARPU = $89, gross margin = 70%, monthly logo churn = 5% → lifetime ≈ 20 months → LTV ≈ $89 × 0.70 × 20.

**Contribution LTV (preferred when COGS known):**

```text
LTV_contribution = Σ expected_monthly_contribution_margin over expected life
```

Until GPU/COGS model lives in `business/finance/`, label LTV **ESTIMATE**.

**LTV:CAC health (planning heuristic):** Aim for **≥3:1** LTV:CAC on a contribution basis once data exists; do not claim achievement without measurement.

---

## 5. Conversion rates

### 5.1 Funnel conversions

```text
Visit→Signup = Signups / Unique_Visitors
Signup→Tester = Tester_Purchases / Signups
Tester→Paid = New_Paid_Subscriptions / Tester_Purchases
Signup→Paid = New_Paid_Subscriptions / Signups
```

### 5.2 Sales conversions (assisted)

```text
Lead→Qualified = Qualified / Leads
Qualified→Demo = Demos_Completed / Qualified
Demo→Proposal = Proposals / Demos_Completed
Proposal→Won = Closed_Won / Proposals
```

Report each with cohort window (e.g., leads created in June, outcomes by 31 July).

---

## 6. LVR — Lead Velocity Rate

**Definition:** Growth rate of qualified leads period-over-period.

```text
LVR = (Qualified_Leads_this_Period − Qualified_Leads_prior_Period)
      / Qualified_Leads_prior_Period
```

Express as percentage. Rising LVR with flat win rate usually precedes revenue growth; falling LVR is an early warning.

Use **sales-qualified leads (SQL)** consistently—see CRM scoring bands Hot/Warm.

---

## 7. Sales cycle length

```text
Cycle_Days = Date_Closed_Won − Date_Lead_Created
```

Report:

- Median cycle (preferred over mean for outliers)  
- By segment (Creator assisted vs Agency vs Enterprise)  
- By source  

Enterprise pilots will run longer than self-serve; never blend without segmentation.

---

## 8. Pipeline metrics

```text
Pipeline_Value = Σ Open_Opportunity_Amounts (Discovery→Negotiation)
Weighted_Pipeline = Σ (Amount_i × Stage_Weight_i)
Pipeline_Coverage = Weighted_Pipeline / New_MRR_Target_for_Period
```

Stage weights: see [`CRM-Workflow.md`](./CRM-Workflow.md).

Also track:

- **Created pipeline** this period  
- **Won pipeline** this period  
- **Lost pipeline** this period  
- **Slippage:** deals whose close date moved out  

---

## 9. Win rate

```text
Win_Rate = Closed_Won / (Closed_Won + Closed_Lost)
```

Variants:

- Win rate from **Proposal** stage only (late-stage win rate)  
- Win rate from **Demo** stage  
- Win rate by competitor presence / loss reason  

Exclude disqualified unauthorized-use leads from win-rate denominator if they never entered Proposal (track separately as DQ rate).

---

## 10. Renewal rate

**Logo renewal rate (enterprise / annual):**

```text
Logo_Renewal_Rate = Accounts_Renewed / Accounts_Up_for_Renewal
```

**Gross revenue retention (GRR):**

```text
GRR = (Starting_MRR − Churned_MRR − Contraction_MRR) / Starting_MRR
```

*(No expansion in numerator.)*

**Net revenue retention (NRR):**

```text
NRR = (Starting_MRR − Churned_MRR − Contraction_MRR + Expansion_MRR) / Starting_MRR
```

For monthly SaaS, define renewal cohort as subscriptions whose billing anniversary or month-N retention you are measuring.

---

## 11. Churn

**Logo churn (monthly):**

```text
Monthly_Logo_Churn = Paying_Customers_Lost_in_Month / Paying_Customers_at_Start_of_Month
```

**Revenue churn (monthly):**

```text
Monthly_Revenue_Churn = MRR_Lost_from_Churn_and_Contraction / MRR_at_Start_of_Month
```

**Voluntary vs involuntary:** Tag payment-failure churn separately—critical while MoR/checkout stabilizes.

**Tester expiry** is not paid churn; do not mix into paid logo churn.

---

## 12. KPI operating dashboard (minimum viable)

| KPI | Cadence | Owner |
|-----|---------|-------|
| MRR / ARR | Weekly | Founder / finance |
| New paid customers | Weekly | Founder |
| Tester→Paid conversion | Weekly | Growth |
| CAC (blended) | Monthly | Growth |
| LTV (estimate) | Monthly | Finance |
| LVR | Monthly | Sales |
| Median cycle | Monthly | Sales |
| Weighted pipeline / coverage | Weekly | Sales |
| Win rate | Monthly | Sales |
| Logo churn / revenue churn | Monthly | CS / founder |
| Renewal rate (when applicable) | Monthly/Quarterly | Sales |
| MoR collection success rate | Weekly | Ops |

---

## 13. Targets vs facts

Roadmap scenario bands in `business/roadmap/BUSINESS_ROADMAP.md` are **planning assumptions**. Do not paste them into public materials as achieved KPIs. Internal targets may reference those bands; external claims require measured evidence.

---

*Measure what the business actually does. Formulas without instrumentation are decoration—instrument CRM and billing next.*
