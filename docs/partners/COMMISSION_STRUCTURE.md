# RTAS Studio AI — Commission Structure

**Status:** **PLACEHOLDER** — not a live public offer  
**Gate:** `AFFILIATE_PAYOUTS_LIVE=false` by default  

---

## Illustrative bands (planning only)

| Plan | Public price | Illustrative first-conversion commission |
|------|--------------|------------------------------------------|
| Tester | $5 · 30 seconds · 5 days | $0 or reduced — discourage $5 farming |
| Standard | $89 / month · 2000 seconds | **20–30%** of first month (assumption) |
| Premium 4K | $249 / month · 2000 seconds | **10–15%** of first month (assumption) |

Base event: first paid conversion (Tester upgrade and/or first subscription month). Final rates confirmed **in writing** before any payout.

---

## Attribution

| Parameter | Source | Default |
|-----------|--------|---------|
| Cookie / window days | `AFFILIATE_COOKIE_DAYS` | 30 |
| Referral query | `?ref=CODE` on pricing / checkout entry | Stub link on dashboard |

Click / signup / paid metrics remain **0** until tracking is connected.

---

## Payout schedule (placeholder)

| Rule | Default env | Notes |
|------|-------------|--------|
| Cadence | Monthly | After payouts enabled |
| Net terms | `AFFILIATE_PAYOUT_NET_DAYS=30` | After month close |
| Minimum | `AFFILIATE_MIN_PAYOUT_USD=50` | Below threshold carries forward |
| Methods | PayPal / Wise / bank | Preference captured on application |

Payment status on dashboard: **Not connected** until rails exist.

---

## Tax & compliance

- Affiliates provide tax / residence country on apply  
- FTC-style disclosure required on promotions  
- Unauthorized likeness / deepfake promotions void eligibility  

---

## What is NOT claimed

- Live payable balances  
- Historical commission totals  
- Number of active affiliates  
- Guaranteed earnings  

See [`AFFILIATE_PROGRAM.md`](./AFFILIATE_PROGRAM.md) and `/affiliate`.
