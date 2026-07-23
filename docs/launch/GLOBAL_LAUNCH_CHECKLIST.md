# Global Launch Checklist

**Phase:** 13 · Sprint 9  
**Runtime source of truth:** `apps/web/src/lib/launch/checklist.ts` (rendered on `/launch` and `/admin/executive`).

Statuses below mirror code. Update the TypeScript checklist when reality changes — do not invent “done.”

---

## Milestones

| ID | Title | Status |
|----|-------|--------|
| m1 | Product freeze (RC) | done |
| m2 | Commercial wiring | in_progress |
| m3 | GTM launch system | in_progress |
| m4 | Paid acquisition start | planned |
| m5 | Press & Product Hunt | planned |

---

## Checklist summary (categories)

### Infrastructure
- [x] Vercel production deploy
- [x] Postgres / Prisma production
- [ ] Fal.ai wallet funded (blocked)
- [ ] Observability vendor sinks (in progress / RFI)

### Security
- [x] Paddle webhook fail-closed
- [x] Auth gates on Studio / generate / checkout
- [x] Admin secret protection
- [ ] CSP enforcement (planned)

### Marketing
- [x] Brand positioning & ICP
- [ ] Launch Center + campaigns (in progress)
- [ ] Asset library fully populated (in progress)
- [ ] Product Hunt runbook execution (planned)

### Sales
- [x] Public pricing $5 / $89 / $249
- [x] Enterprise / demo lead capture
- [ ] Live Paddle purchase → credits E2E (blocked)
- [x] Partners & affiliate applications

### Support
- [x] Help Center surfaces
- [ ] Feedback portal votes/status (in progress)
- [x] Support email routing

### Business
- [x] Legal policies (Terms / Privacy / Refund)
- [ ] Public roadmap published (in progress → ship with Sprint 9)
- [ ] Acquisition dashboard (in progress → ship with Sprint 9)

---

## Owner keys

`founder` · `engineering` · `marketing` · `sales` · `support` · `ops`
