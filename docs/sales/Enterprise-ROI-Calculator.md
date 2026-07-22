# RTAS Studio AI — Enterprise ROI Calculator

**Purpose:** Help buyers estimate return from adopting RTAS Studio AI for recurring video production.  
**Fact policy:** Pricing rows marked **Verified**. All productivity outcomes are **Assumptions / Hypotheticals** unless the buyer substitutes their own data.  
**Product:** https://rtasstudio.com · Plans: Tester $5 · Standard $89/mo · Premium $249/mo · 1 credit = 1 second.

---

## Inputs (buyer-editable)

| Input | Symbol | Example assumption |
|-------|--------|--------------------|
| RTAS plan price / month | \(P\) | $89 (Standard) or $249 (Premium) |
| Traditional cost per finished video | \(C_v\) | $800 (agency/freelancer fully loaded) |
| Videos needed per month | \(N\) | 12 |
| Hours per video (traditional) | \(H_t\) | 10 |
| Hours per video (with RTAS + light edit) | \(H_a\) | 2 |
| Fully loaded creative hourly cost | \(W\) | $45 / hour |
| Employees (FTE) on video today | \(E\) | 2 |
| Output videos / FTE / month today | \(O_t\) | 4 |
| Output videos / FTE / month with RTAS | \(O_a\) | 10 |

---

## Formulas

### 1. Monthly software cost

\[
Monthly\ Cost = P
\]

(Add seats later if multi-seat SKU is sold.)

### 2. Time saved (hours / month)

\[
Time\ Saved = N \times (H_t - H_a)
\]

### 3. Labor savings ($ / month)

\[
Labor\ Savings = Time\ Saved \times W
\]

### 4. Production cost avoided (vendor substitution)

\[
Vendor\ Savings = N \times C_v \times Substitution\%
\]

Use \(Substitution\%\) between 0 and 1 for share of videos that skip external production.

### 5. Employees saved (FTE equivalent)

\[
Employees\ Saved = E \times \left(1 - \frac{O_t}{O_a}\right)
\]

(Only if output target is held constant and capacity was the constraint.)

Alternative capacity view:

\[
FTE\ Needed_{AI} = \frac{N}{O_a},\quad FTE\ Needed_{Trad} = \frac{N}{O_t}
\]

\[
Employees\ Saved = \max(0,\ FTE\ Needed_{Trad} - FTE\ Needed_{AI})
\]

### 6. Production increase (%)

\[
Production\ Increase\% = \left(\frac{O_a}{O_t} - 1\right) \times 100
\]

### 7. Monthly net benefit

\[
Net\ Benefit = Labor\ Savings + Vendor\ Savings - Monthly\ Cost
\]

### 8. ROI %

\[
ROI\% = \frac{Net\ Benefit}{Monthly\ Cost} \times 100
\]

### 9. Payback (months)

For one-time onboarding cost \(S\) (training, integrations):

\[
Payback = \frac{S}{Net\ Benefit}
\]

If \(S = 0\), payback is immediate upon first month of positive net benefit.

### 10. Annual savings

\[
Annual\ Savings = Net\ Benefit \times 12
\]

---

## Worked Example A — Marketing team on Standard (Hypothetical)

**Assumptions**

- Plan: Standard **$89/mo** (Verified price)  
- \(N = 12\) videos/month  
- \(H_t = 8\) hours, \(H_a = 2\) hours  
- \(W = \$40\)/hour  
- Vendor substitution: 50% of videos at \(C_v = \$600\)  
- Onboarding \(S = \$500\)

**Calculations**

| Metric | Work |
|--------|------|
| Time saved | \(12 \times (8-2) = 72\) hours |
| Labor savings | \(72 \times 40 = \$2,880\) |
| Vendor savings | \(12 \times 600 \times 0.5 = \$3,600\) |
| Monthly cost | **$89** |
| Net benefit | \(2880 + 3600 - 89 = \$6,391\) |
| ROI % | \(6391 / 89 \approx \mathbf{7181\%}\) |
| Payback | \(500 / 6391 \approx \mathbf{0.08}\) months |
| Annual savings | \(6391 \times 12 \approx \mathbf{\$76,692}\) |

*Extreme ROI is normal when software replaces agency line items; buyers should stress-test substitution % and quality acceptance rates.*

---

## Worked Example B — Agency pod on Premium (Hypothetical)

**Assumptions**

- Plan: Premium **$249/mo** (Verified price)  
- Team: \(E = 3\) editors/producers  
- \(O_t = 5\) client videos / FTE / month  
- \(O_a = 12\) with RTAS-assisted drafts  
- Hold client delivery at 36 videos/month  
- Labor \(W = \$55\)/hour; traditional hours 6 → AI-assisted 1.5  
- No external vendor substitution (\(Vendor\ Savings = 0\))  
- \(S = \$2,000\) onboarding

**Calculations**

| Metric | Work |
|--------|------|
| Time saved | \(36 \times (6-1.5) = 162\) hours |
| Labor savings | \(162 \times 55 = \$8,910\) |
| FTE needed traditional | \(36 / 5 = 7.2\) (or constrained to 3 FTEs → backlog) |
| FTE needed AI | \(36 / 12 = 3.0\) |
| Employees saved (capacity model) | If previously needing 7.2 vs 3.0 → **4.2 FTE equivalent capacity** unlocked (not necessarily terminated headcount) |
| Production increase % | \((12/5 - 1)\times100 = \mathbf{140\%}\) per FTE |
| Monthly cost | **$249** |
| Net benefit | \(8910 - 249 = \$8,661\) |
| ROI % | \(8661 / 249 \approx \mathbf{3478\%}\) |
| Payback | \(2000 / 8661 \approx \mathbf{0.23}\) months |
| Annual savings | \(\approx \mathbf{\$103,932}\) |

---

## Worked Example C — Conservative corporate (Hypothetical)

**Assumptions**

- Standard **$89**  
- Only **4** videos/month  
- Time 10h → 4h; \(W=\$50\)  
- Substitution 0% (all internal)  
- \(S=\$1,000\)

| Metric | Result |
|--------|--------|
| Time saved | 24 hours |
| Labor savings | $1,200 |
| Net benefit | $1,111 |
| ROI % | ~1,248% |
| Payback | ~0.9 months |
| Annual savings | ~$13,332 |

Still positive under conservative volume—useful for skeptical finance partners.

---

## Credit capacity check (Verified pools)

| Plan | Seconds / month | ≈ Minutes |
|------|----------------:|----------:|
| Tester | 30 (5-day window) | 0.5 |
| Standard | 2,000 | ~33.3 |
| Premium | 2,000 | ~33.3 |

If average video is 15 seconds finished: Standard/Premium support on the order of **~133 clips/month** before overage policy (confirm current overage/upgrade path in product).

Buyers must align \(N \times duration\) with credit pools.

---

## How to run a pilot ROI proof

1. Pick 5 authorized assets; run on **Tester ($5)**.  
2. Measure actual \(H_a\) and acceptance rate vs traditional.  
3. Recompute Net Benefit with **buyer data**.  
4. Expand to Standard or Premium.  
5. Re-evaluate quarterly as templates mature.

---

## Related

[Product-OnePager.md](./Product-OnePager.md) · [Target-Customer-Profiles.md](./Target-Customer-Profiles.md) · [Business-Metrics.md](./Business-Metrics.md)
