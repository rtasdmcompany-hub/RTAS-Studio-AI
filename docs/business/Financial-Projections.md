# RTAS Studio AI — Financial Projections (Illustrative)

**Classification:** Confidential — Board / Investor / M&A planning  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (Pakistan)  
**Phase:** 11 · Sprint 3  
**Currency:** USD  

---

## Critical labels

| Label | Meaning |
|-------|---------|
| **ILLUSTRATIVE** | Scenario math for planning—not a forecast, commitment, or guaranteed outcome |
| **EARLY-STAGE** | Product live; verified historical ARR/EBITDA **not asserted** as the base year |
| **PLANNING ASSUMPTION** | Input chosen for modeling; replace with actuals when available |
| **VERIFIED ANCHOR** | Pricing & product facts used as constants |

**Verified anchors**

| Anchor | Value |
|--------|-------|
| Tester | $5 · 30s · 5 days (treated as **non-ARR** evaluation revenue) |
| Standard | $89 / month · 2000s |
| Premium | $249 / month · 2000s |
| MoR | Paddle (live checkout may still be pending) |

**Cross-links:** `/business/roadmap/BUSINESS_ROADMAP.md` · `Company-Valuation.md` · `/business/sales/ICP.md`

---

## 1. Modeling approach

Three scenarios for Years 1–3 from a commercial “Year 1 = first 12 months of meaningful MoR collection” framing:

| Scenario | Narrative |
|----------|-----------|
| **Conservative** | Slow MoR; weak conversion; higher churn; limited agency |
| **Expected (Base)** | Stable checkout; steady Tester→Standard; light agency outbound |
| **Aggressive** | Strong agency adoption; healthier Premium mix; efficient CAC |

Figures are **annual** unless noted. Monthly views derived for MRR/ARR presentation.

---

## 2. Shared assumptions (all scenarios)

| Assumption | Value | Notes |
|------------|-------|-------|
| Average Standard price | $89 / mo | VERIFIED |
| Average Premium price | $249 / mo | VERIFIED |
| Tester counted in revenue | Yes (small) | **Excluded from ARR** |
| MoR fee burden | ~5–10% of GMV | PLANNING ASSUMPTION (Paddle-class) |
| Hosting / SaaS tools | Scaled with users | Vercel, Supabase, Cloudflare, Resend, Google |
| Inference COGS | Dominant variable cost | Fal wallet; **measure monthly** |
| Target gross margin (post-inference) | 45% / 55% / 65% by scenario maturity | ILLUSTRATIVE; not guaranteed |
| Founder / labor | Included in opex as cash or opportunity | Bootstrap-realistic |
| Tax | Modeled at high level only | Jurisdiction-specific OWNER UPLOAD |
| FX | USD reporting | Local costs may be PKR-denominated |

### Mix assumptions (paying seats, YE)

| Scenario | Standard share | Premium share |
|----------|----------------|---------------|
| Conservative | 90% | 10% |
| Expected | 80% | 20% |
| Aggressive | 70% | 30% |

### Blended ARPU (paying monthly seats)

| Scenario | Blended ARPU / mo |
|----------|-------------------|
| Conservative | 0.9×89 + 0.1×249 = **$105** |
| Expected | 0.8×89 + 0.2×249 = **$121** |
| Aggressive | 0.7×89 + 0.3×249 = **$137** |

---

## 3. Customer growth (paying seats — ILLUSTRATIVE)

Paying seats exclude free/unconverted accounts.

| Year | Conservative EOY seats | Expected EOY seats | Aggressive EOY seats |
|------|------------------------|--------------------|----------------------|
| Y1 | 40 | 100 | 200 |
| Y2 | 90 | 280 | 550 |
| Y3 | 160 | 550 | 1,100 |

**Qualitative growth path:** Tester acquisition → conversion → retention → agency multi-seat expansion (Aggressive).

Illustrative Tester volume (non-ARR):

| Year | Conservative | Expected | Aggressive |
|------|--------------|----------|------------|
| Y1 Tester purchases | 200 | 600 | 1,500 |
| Y2 | 350 | 1,200 | 3,000 |
| Y3 | 500 | 2,000 | 5,000 |

Tester revenue = count × $5 (ILLUSTRATIVE).

---

## 4. MRR / ARR (ILLUSTRATIVE)

ARR ≈ EOY MRR × 12, where EOY MRR ≈ EOY paying seats × blended ARPU.  
(Ignores intra-year ramp shape for simplicity; real diligence should use monthly cohort curves.)

### Year 1

| Metric | Conservative | Expected | Aggressive |
|--------|--------------|----------|------------|
| EOY paying seats | 40 | 100 | 200 |
| EOY MRR | $4,200 | $12,100 | $27,400 |
| EOY ARR | $50,400 | $145,200 | $328,800 |
| Tester revenue (annual) | $1,000 | $3,000 | $7,500 |
| **Total illustrative revenue** | **~$45k–$55k** | **~$120k–$160k** | **~$280k–$360k** |

Revenue vs ARR: mid-year ramp means **recognized subscription revenue ≈ 50–70% of EOY ARR** in Y1. Tables below use **recognized revenue** approximations.

### Recognized revenue approximation method

`Subscription revenue ≈ 0.6 × EOY ARR` in Y1 (ramp), `0.85 × average(EOY ARR_t, EOY ARR_t-1)` in Y2–Y3 for smoother growth—ILLUSTRATIVE only.

---

## 5. Revenue build (Y1–Y3)

### Conservative

| Line | Y1 | Y2 | Y3 |
|------|----|----|-----|
| Subscription revenue | $30,000 | $72,000 | $130,000 |
| Tester & other | $1,000 | $1,800 | $2,500 |
| **Total revenue** | **$31,000** | **$73,800** | **$132,500** |
| EOY MRR | $4,200 | $9,450 | $16,800 |
| EOY ARR | $50,400 | $113,400 | $201,600 |

### Expected (Base)

| Line | Y1 | Y2 | Y3 |
|------|----|----|-----|
| Subscription revenue | $87,000 | $260,000 | $620,000 |
| Tester & other | $3,000 | $6,000 | $10,000 |
| **Total revenue** | **$90,000** | **$266,000** | **$630,000** |
| EOY MRR | $12,100 | $33,880 | $66,550 |
| EOY ARR | $145,200 | $406,560 | $798,600 |

### Aggressive

| Line | Y1 | Y2 | Y3 |
|------|----|----|-----|
| Subscription revenue | $197,000 | $720,000 | $1,650,000 |
| Tester & other | $7,500 | $15,000 | $25,000 |
| **Total revenue** | **$204,500** | **$735,000** | **$1,675,000** |
| EOY MRR | $27,400 | $75,350 | $150,700 |
| EOY ARR | $328,800 | $904,200 | $1,808,400 |

These bands are directionally consistent with `/business/roadmap/BUSINESS_ROADMAP.md` scenario thinking (Low/Base/High), rounded for board readability.

---

## 6. Expense model (ILLUSTRATIVE)

### Cost categories

| Category | Drivers |
|----------|---------|
| Inference COGS (Fal) | Seconds generated × cost/second |
| MoR fees | % of GMV |
| Cloud & tooling | Hosting, DB, email, DNS, monitoring |
| People | Founder draw, contractors, future hires |
| GTM | Ads, content, tools, travel |
| Legal / compliance / finance | Counsel, filings, accounting |
| Contingency | Buffer |

### Expense & margin — Expected (Base)

| Line | Y1 | Y2 | Y3 |
|------|----|----|-----|
| Total revenue | $90,000 | $266,000 | $630,000 |
| Inference COGS | $36,000 | $95,000 | $200,000 |
| MoR & payment fees | $7,000 | $20,000 | $48,000 |
| Cloud & tooling | $12,000 | $22,000 | $40,000 |
| **Gross profit** | **$35,000** | **$129,000** | **$342,000** |
| **Gross margin** | **39%** | **48%** | **54%** |
| People / contractors | $40,000 | $110,000 | $220,000 |
| GTM | $15,000 | $45,000 | $90,000 |
| Legal / G&A | $10,000 | $20,000 | $35,000 |
| **Opex (ex-COGS)** | **$65,000** | **$175,000** | **$345,000** |
| **Operating income (approx. EBITDA proxy)** | **−$30,000** | **−$46,000** | **−$3,000** |
| **Op. margin** | **−33%** | **−17%** | **~0%** |

### Expense & margin — Conservative

| Line | Y1 | Y2 | Y3 |
|------|----|----|-----|
| Total revenue | $31,000 | $73,800 | $132,500 |
| Total COGS (inference+MoR+cloud) | $22,000 | $45,000 | $72,000 |
| Gross profit | $9,000 | $28,800 | $60,500 |
| Gross margin | 29% | 39% | 46% |
| Opex | $45,000 | $70,000 | $95,000 |
| Operating income | −$36,000 | −$41,200 | −$34,500 |
| Op. margin | −116% | −56% | −26% |

### Expense & margin — Aggressive

| Line | Y1 | Y2 | Y3 |
|------|----|----|-----|
| Total revenue | $204,500 | $735,000 | $1,675,000 |
| Total COGS | $85,000 | $265,000 | $560,000 |
| Gross profit | $119,500 | $470,000 | $1,115,000 |
| Gross margin | 58% | 64% | 67% |
| Opex | $120,000 | $320,000 | $650,000 |
| Operating income | −$500 | $150,000 | $465,000 |
| Op. margin | ~0% | 20% | 28% |

---

## 7. Summary dashboard (Expected)

| KPI | Y1 | Y2 | Y3 |
|-----|----|----|-----|
| Revenue | $90k | $266k | $630k |
| EOY ARR | $145k | $407k | $799k |
| EOY MRR | $12.1k | $33.9k | $66.6k |
| EOY paying seats | 100 | 280 | 550 |
| Gross margin | ~39% | ~48% | ~54% |
| Op. income | ~−$30k | ~−$46k | ~$0 |

---

## 8. Cash & funding note (ILLUSTRATIVE)

| Scenario | Y1–Y2 cash character |
|----------|----------------------|
| Conservative | Requires continued operator subsidy |
| Expected | Bootstrap possible with tight burn; optional angel if accelerating GTM |
| Aggressive | May justify seed process if retention proven — funding is optional, not assumed |

No raise is required by this model; it is a **choice** contingent on evidence.

---

## 9. Sensitivities

| Change | Directional impact |
|--------|--------------------|
| MoR live delayed 6 months | Shift Y1 revenue −40% to −70% |
| Inference cost +30% | Gross margin −8 to −12 pts |
| Premium mix +10 pts | ARPU ↑; margin mix depends on 4K COGS |
| Monthly churn 8% vs 3% | Seats & ARR compress sharply by Y3 |
| Agency multi-seat lands | Accelerates Aggressive path |

---

## 10. Management reporting requirements (to replace ILLUSTRATIVE)

When commerce is live, replace this file’s inputs with:

1. Paddle settlements (MRR, refunds, taxes)  
2. Fal spend per day / per second  
3. Cohort retention (D30/D90) and logo churn  
4. CAC by channel  
5. Support tickets per paying seat  

Until then, treat every chart as **scenario scaffolding**.

---

## 11. Explicit non-claims

- Not audited.  
- Not a promise to investors or employees.  
- Not a basis for securities marketing.  
- Not evidence of current ARR.

---

*Companion: `Company-Valuation.md`, `Business-Due-Diligence.md`, `PHASE11-SPRINT3-REPORT.md`.*
