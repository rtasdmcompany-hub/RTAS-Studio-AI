# Churn Prevention

**Implementation:** `apps/web/src/lib/customer-success/churn-prevention.ts`  
**Consumed by:** Customer Health + Retention Center

---

## Principle

**Rule-based recovery only.** No fake AI predictions, propensity scores, or invented churn probabilities.

## Signals (examples)

| Signal | Trigger |
|--------|---------|
| Email unverified | `emailVerified === false` |
| Inactive 10d / 21d | No login or generation activity |
| Low credits | Active sub + ≤10s remaining |
| Expired pool | `creditsExpireAt` in the past with balance |
| Tester expiring | ≤2 days left on Tester window |
| Failed payments | Billing transactions matching failure/cancel rules |
| Open tickets | ≥2 open/waiting tickets |
| No first value | Zero projects or completed videos |
| Paid idle | Active sub + zero gens in 14 days |

## Risk levels

| Level | Score band |
|-------|------------|
| healthy | 0–19 |
| watch | 20–44 |
| at_risk | 45–69 |
| critical | 70–100 |

Recommendations are plain-language next steps (verify email, open Studio, upgrade, reply on tickets, check Billing).
