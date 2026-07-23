# Enterprise Pricing — RTAS Studio AI

**Phase:** 13 · Sprint 2  
**Public SKU truth:** `packages/shared` credits/payments constants

## Commercial naming vs published plans

| Enterprise name | Maps to | Public price | CTA |
|-----------------|---------|--------------|-----|
| **Tester** | Tester | $5 · 30 seconds · 5 days | Self-serve `/pricing` |
| **Creator** | Standard | $89/mo · 2000 seconds | Self-serve `/pricing` |
| **Business** | Premium 4K | $249/mo · 2000 seconds · cinematic 4K | Self-serve `/pricing` |
| **Enterprise** | Custom terms | **No fixed price** | Contact Sales / Request Proposal / Book Demo |

## Rules

1. Never show a fabricated Enterprise list price on marketing pages.
2. Creator/Business copy must disclose Standard/Premium mapping.
3. Volume, procurement, private deployment, dedicated capacity → proposal only.
4. Credit definition remains **1 credit = 1 second** — no “unlimited AI” packaging.

## UI

- Section: `EnterprisePricingSection` on `/enterprise#pricing`
- Source: `apps/web/src/lib/enterprise/pricing.ts`
