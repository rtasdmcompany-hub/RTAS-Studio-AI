# Conversion Optimization — RTAS Studio AI

**Phase:** 13 · Sprint 3

---

## Principles

1. Honest CTAs — never imply free generation credits.
2. One primary action per viewport section.
3. Context-aware upgrade prompts (credits needed vs available).
4. No misleading urgency (no fake countdowns / scarcity).
5. Prove with live analytics events — blank rates OK.

---

## CTA matrix

| Page | Primary | Secondary |
|------|---------|-----------|
| Homepage | Start creating → `/studio` | View pricing |
| Pricing | Get Tester / Go Standard / Go Premium | — |
| Features | Start creating | Compare plans |
| Enterprise | Schedule demo | Enterprise inquiry |
| Blog | Start creating | View pricing |
| Docs | Open Studio | How to use |
| Support | Help Center | Contact support |
| Updates | Subscribe | Start creating |

Canon: `apps/web/src/lib/conversion-ctas.ts`

---

## High-impact friction fixes shipped

- Docs copy: removed “free tiers” preview implication; clarify 0 starting credits.
- Features / blog / docs final CTAs aligned to honest labels.
- Paywall: plan compare rows + current-tier hints + no urgency copy.
- Lead capture: footer + `/updates` with privacy consent.

---

## Experiments (proposed — not fabricated results)

| Test | Hypothesis | Guardrail |
|------|------------|-----------|
| Homepage secondary “Get Tester” | Increases paid evaluation | Monitor Tester checkouts only |
| Retention upgrade card | Increases Standard from Tester | Use real billing events |
