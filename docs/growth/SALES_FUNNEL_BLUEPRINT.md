# RTAS Studio AI — Sales Funnel Blueprint

**Classification:** Growth / sales ops  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Sprint:** Phase 11 · Sprint 8  
**Integrity:** Stage definitions and formulas only. Conversion rates left blank until real data.

---

## Funnel purpose

Convert strangers into **paying** users of Tester, Standard, or Premium—then expand seats—while staying honest about MoR/checkout readiness and the absence of a free credit plan.

Cross-links: [`business/sales/ICP.md`](../../business/sales/ICP.md) · [`CUSTOMER_ACQUISITION_STRATEGY.md`](CUSTOMER_ACQUISITION_STRATEGY.md) · [`PRICING_OPTIMIZATION.md`](PRICING_OPTIMIZATION.md) · [`docs/launch/SALES-ONE-PAGER.md`](../launch/SALES-ONE-PAGER.md)

---

## Dual motion

| Motion | Who | Path |
|--------|-----|------|
| **Self-serve** | Creators, startups, small teams | Visit → Signup → Tester or Standard checkout → Studio usage → Upgrade |
| **Founder-assisted** | Agencies, marketing companies, enterprise pilots | Outbound / inbound lead → Discovery → Demo → Paid start → Expand |

Both motions share the same economic ladder: **Tester ($5) → Standard ($89/mo) → Premium ($249/mo) → multi-seat / custom**.

---

## Stage map

| # | Stage | Definition | Exit criteria |
|---|-------|------------|---------------|
| 0 | **Aware** | Visited rtasstudio.com or touched outbound | Landing session or reply |
| 1 | **Interested** | Viewed pricing / features / showcase | Clear intent signal (pricing view, demo ask) |
| 2 | **Signed up** | Account created | Verified email / session able to open Studio |
| 3 | **Activated (product)** | First meaningful Studio action (project or generate attempt) | User understands credit paywall if 0 credits |
| 4 | **First revenue** | Successful Tester or subscription checkout via Paddle | Paid event recorded |
| 5 | **Value realized** | Successful generation completed; output reviewed | User has usable asset |
| 6 | **Retained** | Standard/Premium renews or Tester converts to subscription | Active paid period |
| 7 | **Expanded** | Upgrade Standard→Premium and/or additional seats | Higher MRR |

**Blocker note:** If stage 4 fails due to pending Paddle approval, treat as system failure—not marketing failure.

---

## Self-serve path (detail)

```
Traffic → Home / Pricing / Showcase
       → Signup
       → Dashboard / Studio
       → Paywall awareness (0 credits if free)
       → Tester ($5) OR Standard ($89) OR Premium ($249)
       → Generate → Output
       → (if Tester) Convert within 5 days → Standard/Premium
       → Renew / Upgrade / Multi-seat
```

**Critical honesty beat:** Free accounts do not receive free seconds. Messaging must push **Tester** as the low-risk paid proof—not a phantom free tier.

---

## Assisted sales path (detail)

| Step | Action | Asset |
|------|--------|-------|
| 1 | ICP list build | [`ICP.md`](../../business/sales/ICP.md) |
| 2 | Short outbound | USP one-liner + rtasstudio.com |
| 3 | Discovery (15–20 min) | Jobs-to-be-done, monthly video volume, brand-safety needs |
| 4 | Demo | Live Studio; credit math; Trust & Safety posture |
| 5 | Commercial close | Tester for proof **or** Standard/Premium for production |
| 6 | Onboarding handoff | Customer success framework |
| 7 | Expand | Premium mix; additional seats; later enterprise discussion |

**Disqualify fast:** Unauthorized likeness requests; free unlimited demands; immediate Fortune-500 procurement with no pilot.

---

## Conversion formulas (track; values blank)

| Metric | Formula |
|--------|---------|
| Visit→Signup | `signups / unique visitors` |
| Signup→Activated | `activated / signups` |
| Signup→Paid | `first_paid / signups` |
| Tester→Standard | `standard_starts_from_tester / tester_starts` (within 14 days) |
| Standard→Premium | `premium_upgrades / standard_accounts` (within 60 days) |
| Lead→Opportunity (assisted) | `qualified_opps / assisted_leads` |
| Opportunity→Close | `closed_won / qualified_opps` |
| Seat expansion rate | `accounts_with_2plus_seats / paid_accounts` |

Populate in [`GROWTH_METRICS_DASHBOARD.md`](GROWTH_METRICS_DASHBOARD.md).

---

## Objection handling (funnel-ready)

| Objection | Response posture |
|-----------|------------------|
| “Is there a free plan?” | No free credits today. Tester is $5 / 30 seconds / 5 days to prove the pipeline. |
| “Why Premium if same 2000 seconds?” | Quality / 4K cinematic positioning—not more seconds. |
| “Are you enterprise-ready?” | Strong legal/trust foundation; enterprise is pilot-first. Start Premium or multi-seat. |
| “Deepfake / face-swap?” | Not offered. Identity Preservation is for authorized content only. |
| “Checkout failed” | Known MoR/domain dependency—escalate ops; do not blame the lead. |

---

## Pipeline hygiene (assisted)

| Field | Required |
|-------|----------|
| Persona (ICP) | Yes |
| Intended first SKU | Tester / Standard / Premium |
| Seat estimate | Number |
| Next step date | Yes |
| Blocker | Checkout / legal / budget / quality / other |

No fake closed-won entries. No logo claims without permission.

---

## SLA targets (internal planning assumptions)

| Motion | Target response |
|--------|-----------------|
| Inbound contact@ / info@ | Same business day |
| Support@ for paid | As published in customer success framework |
| Outbound follow-up | Within 48 hours of reply |

---

## Weekly funnel review (founder)

1. Checkout health (Paddle)  
2. New signups and first-paid count  
3. Tester conversions  
4. Assisted pipeline moves  
5. Top drop-off stage and one fix  

---

*Companions: [`CUSTOMER_SUCCESS_FRAMEWORK.md`](CUSTOMER_SUCCESS_FRAMEWORK.md) · [`REVENUE_STRATEGY.md`](REVENUE_STRATEGY.md) · [`ENTERPRISE_EXPANSION_PLAN.md`](ENTERPRISE_EXPANSION_PLAN.md)*
