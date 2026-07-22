# RTAS Studio AI — Board Governance Framework

**Classification:** Confidential — Governance / corporate development  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 9  

**Purpose:** Practical governance for an **early-stage, founder-centric** SaaS—enough structure for investment or acquisition diligence without pretending a large public-company board already exists.

**Integrity:** No invented board members, investors with seats, or historical meeting minutes. Where a formal board does not yet exist, this framework describes **how to operate and what to create**.

---

## 1. Current-state assumption (honest)

| Topic | Working assumption | Label |
|-------|--------------------|-------|
| Control | Founder / operator-led decisions under RTAS Digital Marketing Company | VERIFIED pattern in docs; confirm legal ownership in VDR |
| Formal board of directors | May be **N/A yet** or informal | Do not invent directors |
| Advisors | Optional; none claimed here | — |
| Minute book | Likely incomplete | OWNER UPLOAD / create going forward |

This framework is **forward-looking operating policy** plus diligence hygiene—not a claim that all rituals already run.

---

## 2. Governance objectives

1. Protect legal and AUP integrity (Identity Preservation; no deepfake marketing drift).  
2. Keep MoR / checkout truth visible to decision-makers.  
3. Separate **day-to-day product ops** from **equity, debt, sale, and exclusivity** decisions.  
4. Reduce key-person opacity for investors and acquirers.  
5. Create an auditable trail before any LOI or fundraising close.

---

## 3. Decision rights matrix

| Decision class | Examples | Authority | Record |
|----------------|----------|-----------|--------|
| **L1 — Operating** | Pricing experiments within published tiers, content, support SLAs, roadmap sequencing | Founder / operator | CRM + weekly notes |
| **L2 — Material commercial** | Partner exclusivity > 6 months, multi-seat custom contracts, large discounts | Founder; counsel if novel legal risk | Written approval log |
| **L3 — Capital** | SAFE/equity raise, debt, major CAPEX | Owners / board (or founder if sole owner—document) | Resolutions + counsel |
| **L4 — Change of control** | Asset sale, equity sale, merger, exclusive M&A process | Owners / board | Formal resolutions; counsel mandatory |
| **L5 — Trust & compliance** | Material AUP policy change, public repositioning on likeness | Founder + legal@ review | Versioned legal change |

**Rule:** L3–L4 never close on chat messages alone.

---

## 4. Recommended meeting cadence (PLANNING)

| Forum | Cadence | Agenda core | Participants |
|-------|---------|-------------|--------------|
| Ops standup | Weekly | MoR status, incidents, support, shipping | Founder + eng/support as available |
| Commercial review | Weekly / biweekly | Pipeline, conversion, partner pilots | Founder |
| Governance check-in | Monthly | Risks, legal changes, cash, access matrix updates | Founder (+ advisor if any) |
| Owner / board session | Quarterly or ad hoc for L3–L4 | Capital, sale, major strategy | Owners / board |

If no formal board exists, the **monthly governance check-in** still produces dated notes suitable for a future minute book.

---

## 5. Minimum board / owner information pack

Distribute before any L3–L4 decision:

1. MoR / checkout status (factual, dated).  
2. Cash and GPU wallet runway (actuals—not invented).  
3. Product incidents / Trust & Safety events.  
4. Pipeline summary (if CRM live) without fake forecasts.  
5. Open legal/compliance issues.  
6. For M&A: [`EXECUTIVE_SUMMARY_FOR_BUYERS.md`](./EXECUTIVE_SUMMARY_FOR_BUYERS.md) + valuation memo **as methodological context only**.

---

## 6. Conflicts, related parties, and RTAS ecosystem

| Topic | Policy |
|-------|--------|
| RTAS Digital Marketing Company services alongside SaaS | Disclose related-party nature to investors/buyers; separate SOWs |
| Founder time allocation | Document approximate split product vs services if material |
| Self-dealing | Arm’s-length pricing; written approval for material related-party deals |
| Personal vs company assets (domain, accounts) | Migrate to entity control; record in IP memo |

---

## 7. Access, security, and continuity (governance-critical)

Maintain a living **access control matrix** (also required for VDR):

| System | Primary owner | Backup | 2FA | Notes |
|--------|---------------|--------|-----|-------|
| Domain DNS / registrar | TBD founder | TBD | Required | Transfer readiness |
| Vercel / hosting | TBD | TBD | Required | |
| Supabase / DB | TBD | TBD | Required | |
| GitHub | TBD | TBD | Required | Branch protection |
| Paddle | TBD | TBD | Required | MoR |
| Fal / GPU | TBD | TBD | Required | COGS |
| Email (Resend / Google) | TBD | TBD | Required | |
| Analytics | TBD | TBD | Required | |

**Governance rule:** No single cloud admin without a documented backup path within 30 days of adopting this framework.

---

## 8. Policies the “board” (or sole owner) should endorse

| Policy | Source of truth |
|--------|-----------------|
| Legal suite v1.1 | Live site + shared legal modules |
| No unauthorized deepfake marketing | Trust & Safety / AI Policy / Terms AUP |
| Fundraising gates | `docs/investors/FUNDRAISING_STRATEGY.md` |
| M&A process phases | `ACQUISITION_STRATEGY.md` |
| Secrets / VDR hygiene | `DATA_ROOM_READINESS.md` · `docs/SECURITY.md` |
| Pricing book | Tester $5 / Standard $89 / Premium $249; 1 credit = 1 second |

Endorsement can be a simple dated owner resolution: “Adopted Phase 11 Sprint 9 governance framework.”

---

## 9. Committee structure (optional, later)

Only add when complexity warrants:

| Committee | When to create |
|-----------|----------------|
| Audit / finance | After meaningful recurring revenue or external investors |
| Compensation | After multiple employees |
| M&A special committee | If conflicted sale process |

Until then, keep a **single decision chain** with counsel on L3–L4.

---

## 10. Minute book starter template

For each owner/board session, record:

- Date, attendees, conflicts disclosed  
- Materials reviewed (titles + dates)  
- Decisions (L-level)  
- Follow-ups with owners and due dates  
- Explicit non-approvals  

Store outside public git (secured VDR folder `01-Corporate/Minutes`).

---

## 11. Diligence narrative for buyers/investors

**Say:** “We are founder-operated with a written governance framework, legal v1.1, and escalating approval for capital and change-of-control; formal board expansion is stage-dependent.”

**Do not say:** Invented independent directors, fake audit committees, or historical minutes that were never held.

---

## 12. Founder actions

1. Confirm legal ownership of product assets vs personal accounts.  
2. Fill the access matrix with real names and backups.  
3. Start monthly dated governance notes (even solo).  
4. Adopt L1–L5 decision rights in writing.  
5. Engage counsel before L3–L4 documents.  
6. Upload any existing resolutions to VDR; else file N/A statement.

---

*Phase 11 Sprint 9 · Governance readiness: **Partial** (framework Complete; formal board artifacts may be Missing/N/A).*
