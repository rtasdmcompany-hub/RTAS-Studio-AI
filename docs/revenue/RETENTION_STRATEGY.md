# Retention Strategy — RTAS Studio AI

**Phase:** 13 · Sprint 3

---

## Customer Retention Center

**Surface:** Dashboard `/profile` → `#retention-center`  
**Component:** `CustomerRetentionCenter.tsx`

Includes:

- Usage summary (remaining credits, plan, jobs in view)
- Context-aware upgrade suggestion (no fake urgency)
- Release notes pointer (`/help/changelog`)
- Learning & support links
- Referral invitation shell labeled **Proposed**

---

## Plays

| Trigger | Play |
|---------|------|
| 0 credits | Get Tester / compare plans |
| Tester depleted | Suggest Standard monthly |
| Standard active | Optional Premium 4K education |
| Churned (inactive + 0 credits) | Reactivate CTA |
| Premium active | CS / Help Center |

---

## Integrity

- Only the signed-in user’s data
- Referral not claimed as live
- No invented NPS / retention %
