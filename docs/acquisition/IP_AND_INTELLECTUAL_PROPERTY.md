# RTAS Studio AI — IP and Intellectual Property

**Classification:** Confidential — Legal / M&A / Investment  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 9  

**Hard rules:**

- **No invented trademarks, patents, copyright registrations, or exclusive model ownership.**  
- Status labels: **Verified** · **Asserted operator control (unregistered)** · **Third-party licensed** · **Missing / to confirm** · **Not claimed**.  
- This memo inventories diligence topics; it is **not** a legal opinion. Counsel owns registration and assignment instruments.

**Cross-links:** Sprint 3 valuation IP section · [`docs/business/Technical-Due-Diligence.md`](../business/Technical-Due-Diligence.md) · [`docs/business/Acquisition-Readiness-Checklist.md`](../business/Acquisition-Readiness-Checklist.md) · [`DATA_ROOM_READINESS.md`](./DATA_ROOM_READINESS.md) · live legal pages.

---

## 1. Executive summary

RTAS Studio AI’s transferable intellectual property is primarily **product software, commercial packaging, brand identity, documentation, and trust/legal drafting**, operated under RTAS Digital Marketing Company. Foundation model weights and many cloud services are **third-party licensed**, not RTAS-owned patents or exclusive AI IP.

Formal trademark/patent registration packages are **not asserted as complete** in this repository. Buyers and investors should treat chain-of-title and registration cleanup as a **standard early-stage workstream**, not as proof of absence of product IP.

---

## 2. Asset inventory

### 2.1 Product software and systems

| Asset | Description | Status |
|-------|-------------|--------|
| Web application | Next.js studio, dashboard, billing UX, marketing surfaces | Asserted operator control (unregistered copyright as default law may apply—**confirm jurisdiction with counsel**) |
| Backend / workers | FastAPI generation gateway, job orchestration | Asserted operator control |
| Shared commercial packages | Credits, pricing constants, categories, legal content modules | Asserted operator control |
| Repositories | Monorepo used in production | Asserted operator control — confirm GitHub org ownership and access |
| Documentation | Architecture, security, ops, business packs | Asserted operator control |
| Database schemas / Prisma models | Application data model | Asserted operator control |

**Diligence question:** Are all contributors (employees/contractors) covered by written IP assignment?

### 2.2 Brand and domain

| Asset | Status | Notes |
|-------|--------|-------|
| Product name “RTAS Studio AI” | Asserted operator control (unregistered) | Used publicly on https://rtasstudio.com |
| Operator “RTAS Digital Marketing Company” | Verified as stated operator in legal/business packs | Entity extracts OWNER UPLOAD |
| Domain rtasstudio.com | Verified live | Registrar ownership proof → VDR upload; transfer readiness to confirm |
| Visual brand / logos | Partial | Live site assets; formal brand kit may still be thin (`business/branding/`) |
| Registered trademarks (word/device) | **Not claimed** in this pack | Do not invent serial numbers; file only if/when counsel advises |
| Registered patents / pending applications | **Not claimed** | None asserted |

### 2.3 Legal and policy content

| Asset | Status |
|-------|--------|
| Terms, Privacy, Refund, Cookies, AI Policy, Trust & Safety v1.1 | Verified live; operator-controlled drafting |
| Acceptable Use / Identity Preservation framing | Verified in product legal posture |
| Legal documentation sign-off | Verified (`docs/LEGAL_DOCUMENTATION_SIGNOFF.md`) |

**Note:** Policy text is an intangible trust asset; it is not a patent.

### 2.4 Data and customer content

| Asset | Status | Notes |
|-------|--------|-------|
| User account data | Subject to Privacy Policy | Transfer requires legal review |
| Generated videos / library assets | Subject to Terms / entitlements | Customer rights persist per contract |
| Marketing analytics | Partial | Tooling early; no invented metrics |

RTAS does **not** claim ownership of customer-uploaded identity assets beyond license grants in Terms.

### 2.5 Third-party / licensed technology (not RTAS exclusive IP)

| Dependency class | Examples (stack truth) | IP posture |
|------------------|------------------------|------------|
| Generative inference | Fal (primary path) and peer providers | **Third-party licensed** — no claim of owned foundation weights |
| Hosting / edge | Vercel, Cloudflare | Third-party service |
| Data / auth | Supabase / Prisma stack | Third-party service + OSS |
| Email | Resend | Third-party service |
| Payments MoR | Paddle | Third-party MoR — checkout activation may be pending |
| Open-source libraries | npm / PyPI dependencies | OSS licenses — SBOM **Partial** |

**Acquirer implication:** Continuity depends on account transfers and license compliance, not on exclusive model patents.

---

## 3. What RTAS can credibly claim vs cannot

| Claim | Allowed? |
|-------|----------|
| “We operate a production SaaS codebase and brand for RTAS Studio AI” | Yes — consistent with shipped product |
| “We own foundation model weights / exclusive video model IP” | **No** |
| “We hold patents protecting our generation method” | **No** (not claimed) |
| “We hold registered trademarks in all target markets” | **No** (not claimed) |
| “Legal suite v1.1 is live and AUP-aligned in marketing posture” | Yes — verified |
| “Pricing and credit semantics are product IP / commercial design” | Yes — as product packaging, not as patent |

---

## 4. Chain-of-title readiness

| Workstream | Rating | Founder / counsel action |
|------------|--------|--------------------------|
| Identify all code contributors | Missing / to confirm | Roster + commit authorship review |
| Contractor / employee IP assignment agreements | Missing | Execute or remediate |
| Confirm repo org ownership | Partial | GitHub org + 2FA + admin list in access matrix |
| Domain registrant = operating entity or assignable | Partial | Registrar proof in VDR |
| Brand asset ownership (logo files) | Partial | Centralize sources |
| Open-source license compliance review | Partial | Produce SBOM + notices |
| Customer contract assignment clauses | Partial | Review Terms; MoR may affect merchant-of-record novation |
| Trademark clearance / filing plan | Not claimed | Optional future; counsel-owned |
| Patent strategy | Not claimed | Generally not primary for this stage |

**Overall IP deal readiness:** **Partial** (aligned with Sprint 3 checklist).

---

## 5. Deal transfer checklist (asset or equity sale)

1. Schedule of IP assets (this memo + exhibits).  
2. Assignment agreement: code, brand, domain, docs → buyer or buyer’s NewCo.  
3. Third-party contract consents (Paddle, Fal, Vercel, Supabase, Cloudflare, Resend, domain registrar).  
4. Open-source disclosure schedule.  
5. Privacy/Terms update or novation plan for users.  
6. Escrow or source delivery mechanics (counsel).  
7. Post-close brand use (RTAS ecosystem coexistence rules).

---

## 6. Infringement and freedom-to-operate posture (honest)

| Topic | Posture |
|-------|---------|
| Competitive category crowded | Acknowledged — differentiate on packaging/trust, not exclusive model claims |
| Formal FTO opinion | **Missing** — not invented; obtain if counsel requires for a process |
| Content misuse risk | Mitigated by Trust & Safety / AI Policy / AUP marketing discipline — not eliminated |
| Dependency license conflict | Manage via SBOM and upgrades |

---

## 7. Recommended near-term IP hygiene (founder actions)

1. Write a one-page **contributor roster** and mark assignment status.  
2. Execute contractor IP assignment templates (counsel).  
3. Export domain WHOIS/registrar ownership proof to secured VDR.  
4. Build admin access matrix (GitHub, Vercel, DNS, Supabase, Paddle, Fal, email).  
5. Generate dependency license inventory (SBOM lite).  
6. Decide with counsel whether to file trademarks for “RTAS Studio AI” in priority markets—**only if budget and clearance support; do not backdate**.  
7. Keep public materials free of fake “patented” or “trademarked” language until registrations exist.

---

## 8. Explicit non-claims

- No patent numbers, trademark registration numbers, or copyright registration certificates are listed because none are asserted as facts in this pack.  
- No third-party company is said to have licensed RTAS IP outbound.  
- No valuation of IP is restated as fact; see methodological bands in `Company-Valuation.md` if needed for internal planning.

---

*Phase 11 Sprint 9 · IP readiness: **Partial** · No fake registrations.*
