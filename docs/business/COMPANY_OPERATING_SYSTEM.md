# RTAS Studio AI — Company Operating System

**Purpose:** How the company decides, cycles, measures, meets, and executes.  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 10  
**Status:** **Planned / Recommended** operating system grounded in **Verified** product & legal facts. Founder-operated today (no separate NOC / CSM team asserted).

**Related:** [`docs/operations/OPERATIONS_MANUAL.md`](../operations/OPERATIONS_MANUAL.md) · [`docs/business/sales/CRM-Workflow.md`](./sales/CRM-Workflow.md) · [`docs/investors/BOARD_MEETING_TEMPLATE.md`](../investors/BOARD_MEETING_TEMPLATE.md)

---

## 1. Operating principles

1. **Truth over theater** — Verified facts only in public and investor materials.  
2. **MoR before media** — Do not scale paid acquisition into unreliable checkout.  
3. **AUP is strategy** — Trust & Safety protects distribution and payments.  
4. **Process beats memory** — CRM + spreadsheet + weekly note.  
5. **Stage-appropriate ambition** — Enterprise motion follows pilot proof; certifications are goals, not claims.  
6. **Single owner, clear RACI** — Until headcount grows, founder owns Ops / Sales / Support with documented playbooks.

---

## 2. Decision rights (RACI lite)

| Decision | Accountable | Consult | Inform |
|----------|-------------|---------|--------|
| Production deploy / rollback | Founder-Eng | — | Support notes |
| Pricing / live SKU changes | Founder | Legal/MoR implications | Site + sales collateral |
| Paid acquisition spend | Founder | Growth docs | Weekly metrics |
| Enterprise proposal / discount | Founder | Sales playbook | CRM |
| Fundraising / M&A process | Founder | Counsel (Recommended) | Board/advisors if any |
| AUP / Trust & Safety exceptions | Founder | Legal pages | Refuse by default |
| Vendor account changes | Founder | Vendor Mgmt doc | Ops log |

---

## 3. Cadence calendar

| Cycle | Ritual | Duration | Primary artifacts |
|-------|--------|----------|-------------------|
| **Daily** | Health + inbox triage | 20–40 min | `/api/health`, `/api/ready`, support@ |
| **Weekly** | Pipeline + MoR + metrics | 60–90 min | CRM, Paddle, Fal, spreadsheet |
| **Biweekly** | GTM experiment review | 45 min | Channel notes; kill/keep |
| **Monthly** | Board-style business review | 90 min | Board template; scorecard deltas |
| **Quarterly** | Strategy + roadmap gate | ½ day | Roadmap scenarios; raise/bootstrap |
| **Annual** | Entity / compliance refresh | 1 day | Legal version check; vendor renewals |

Engineering ops detail: Operations Manual. Business review template: Board Meeting Template.

---

## 4. KPI dictionary (measure when available)

Values intentionally blank until instrumented. Formulas exist in sales/growth packs.

### 4.1 Commercial

| KPI | Definition | Target policy |
|-----|------------|---------------|
| MoR collections (gross) | Paddle payouts / sales export | Track actuals only |
| Net collections | Gross − refunds − fees | Track actuals only |
| Paying accounts | Active paid seats by plan | Track actuals only |
| Tester → Paid % | Paid starts / Tester starts (cohort) | Set target after n≥30 |
| MRR / ARR | Standard definition; Collected vs Contracted | No public claim until verified |
| ARPU | MRR / paying accounts | Derived |

### 4.2 Funnel & sales

| KPI | Definition |
|-----|------------|
| Leads created | CRM new records |
| Discovery → Demo | Conversion |
| Demo → Pilot / Paid | Conversion |
| Win rate | Wins / closed opportunities |
| Sales cycle days | Create → close |
| Pipeline coverage | Weighted pipeline / next-90-day goal |

### 4.3 Product & ops

| KPI | Definition |
|-----|------------|
| Site availability | Health/ready success |
| Generation success proxy | Fail rate from logs / Fal |
| Support first response | Time to first human reply |
| Sev-1 incidents | Count + MTTR |
| Fal spend / second | COGS proxy |

### 4.4 Trust

| KPI | Definition |
|-----|------------|
| AUP incidents | Confirmed misuse cases |
| Paddle compliance flags | Account warnings / holds |
| Refund rate | Refunds / transactions |

**Rule:** Empty is better than fabricated. Dashboard: [`docs/growth/GROWTH_METRICS_DASHBOARD.md`](../growth/GROWTH_METRICS_DASHBOARD.md).

---

## 5. Meeting system

| Meeting | Attendees (today) | Agenda (fixed) | Output |
|---------|-------------------|----------------|--------|
| Weekly Ops | Founder (± contractor) | MoR · health · incidents · Fal · email | Action list ≤5 |
| Weekly Pipeline | Founder | New · stage moves · forecast · losses | CRM hygiene |
| Monthly Business Review | Founder (± advisor) | Scorecard · cash · GTM · risks · decisions | 1-page minutes |
| Incident bridge | Founder | Severity · customer impact · comms · fix | Postmortem note |

No vanity standups. If a meeting has no decision or hygiene output, cancel it.

---

## 6. Execution system (how work moves)

```
Idea / inbound
    → Capture (CRM or ops log)
    → Classify (Support / Sales / Eng / Finance / Legal)
    → Priority (P0 MoR/security · P1 revenue · P2 polish · P3 later)
    → Owner + due date
    → Done criteria written
    → Review in weekly ritual
```

**P0 always includes:** checkout broken, auth down, security incident, Paddle hold, data loss risk.

Change classes & rollback: [`docs/operations/CHANGE_MANAGEMENT.md`](../operations/CHANGE_MANAGEMENT.md).  
SOPs: [`docs/operations/STANDARD_OPERATING_PROCEDURES.md`](../operations/STANDARD_OPERATING_PROCEDURES.md).

---

## 7. GTM operating modes

| Mode | When | Rules |
|------|------|-------|
| **Self-serve** | Default for Tester/Standard | Site + email support; no custom contracts |
| **Assisted** | Agencies, Premium, pilots | Demo script + proposal template |
| **Enterprise exploration** | Named design partners | Pilot-first; no fake SSO/SLA |
| **Pause paid growth** | MoR red or CAC unmeasurable | Organic + outbound only |

Playbooks: [`docs/business/sales/Go-To-Market-Strategy.md`](./sales/Go-To-Market-Strategy.md) · [`docs/growth/CUSTOMER_ACQUISITION_STRATEGY.md`](../growth/CUSTOMER_ACQUISITION_STRATEGY.md).

---

## 8. Risk & compliance loop

| Cadence | Action |
|---------|--------|
| Weekly | Scan Risk Register top 5 (esp. MoR R-01) |
| Monthly | Compliance Register goals vs implemented |
| On change | Update Trust & Safety / Terms only via controlled legal process |
| Always | No invented certifications (SOC 2 / ISO / GDPR cert) |

Registers: [`RISK_REGISTER.md`](../operations/RISK_REGISTER.md) · [`COMPLIANCE_REGISTER.md`](../operations/COMPLIANCE_REGISTER.md).

---

## 9. People system (current → next)

| Now (Verified stage) | Next hire triggers (**Recommended**) |
|----------------------|--------------------------------------|
| Founder = Eng + Ops + Sales + Support | First contractor support when paid ticket volume exceeds RTA |
| No dedicated CSM | Part-time CS when Premium/agency seats justify |
| No formal board | Advisor cadence monthly; formal board if raise |

Team roadmap: [`docs/investors/TEAM_ROADMAP.md`](../investors/TEAM_ROADMAP.md).

---

## 10. Information architecture

| Layer | System of record |
|-------|------------------|
| Product truth | Live site + shared packages + engineering docs |
| Legal truth | rtasstudio.com legal pages v1.1 + sign-off |
| Business strategy | `/business/` + `/docs/business/` master pack |
| Sales process | `/docs/business/sales/` + CRM |
| Investor narrative | `/docs/investors/` + `/docs/sales/` |
| Ops control | `/docs/operations/` |
| Growth experiments | `/docs/growth/` + spreadsheet |
| Corp-dev | `/docs/acquisition/` + VDR index |

**Single front door:** [`BUSINESS_MASTER_INDEX.md`](./BUSINESS_MASTER_INDEX.md).

---

## 11. Kill switches (Recommended)

Stop or freeze the following if triggered:

| Trigger | Action |
|---------|--------|
| Checkout failure rate unacceptable | Pause paid ads + new enterprise promises |
| Paddle AUP warning | Immediate marketing copy review |
| Fal balance / generation outage | Status note; pause demos that require live gen |
| Support backlog > RTA for 7 days | Cap outbound; clear inbox |
| Founder burnout signal | Drop P3; keep P0/P1 only |

---

## 12. Adoption checklist (first 14 days of Phase 12)

- [ ] Pin MoR status sentence in CRM  
- [ ] Create metrics spreadsheet from KPI dictionary  
- [ ] Schedule weekly Ops + Pipeline on calendar  
- [ ] Schedule first monthly Business Review  
- [ ] Open Risk Register and confirm R-01 owner = founder  
- [ ] Read Founder Master Playbook once end-to-end  

---

*Company Operating System — Phase 11 Sprint 10 · RTAS Studio AI*
