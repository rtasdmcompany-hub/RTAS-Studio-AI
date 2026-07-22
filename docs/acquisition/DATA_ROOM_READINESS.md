# RTAS Studio AI — Data Room Readiness Checklist

**Classification:** Confidential — M&A / Investment diligence ops  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 9  

**Purpose:** Operating checklist to stand up a **secured external virtual data room** (VDR). Complements—does not replace—the Sprint 3 index at [`docs/business/Virtual-Data-Room-Index.md`](../business/Virtual-Data-Room-Index.md).

**Honesty rules:**

- Do **not** put live secrets, API keys, PANs, or production credentials in git.  
- Ratings: **Ready** (can share under NDA now) · **Partial** · **Not ready** · **N/A yet**.  
- Empty cells must not be filled with invented filings or metrics.

---

## 1. Overall readiness

| Layer | Rating | Notes |
|-------|--------|-------|
| Index / taxonomy | **Ready** | Sprint 3 VDR index + this checklist |
| In-repo documentation | **Ready** | Architecture, legal pointers, business packs |
| Secured external room (Drive/DD platform) | **Partial** | Must be created/mirrored by founder when process opens |
| Corporate / ownership uploads | **Not ready** | Cap table, registries OWNER UPLOAD |
| Financial actuals uploads | **Not ready** | MoR/bank exports missing |
| Source-code diligence access | **Partial** | Repo exists; controlled guest access process incomplete |
| **Overall data room readiness** | **Partial** | Fine for early NDA chats; not institutional DD-complete |

---

## 2. Administration checklist

| # | Item | Rating | Action if not Ready |
|---|------|--------|---------------------|
| A1 | Choose VDR platform (Google Drive / Dropbox / dedicated DD) | Not ready | Founder selects; enable 2FA |
| A2 | Folder tree mirrors Sprint 3 index | Partial | Create 00–Admin through Roadmap folders |
| A3 | NDA template | Not ready | Counsel-provided |
| A4 | Access log (who/when) | Not ready | Enable platform audit |
| A5 | Permission matrix (View vs Download) | Not ready | Default View-only for early buyers |
| A6 | Watermark / disable print (optional) | N/A yet | Enable if counsel advises |
| A7 | Document version dating convention | Partial | Use YYYY-MM-DD prefixes |
| A8 | Secrets policy (no keys in VDR) | Ready | Documented here + security docs |

---

## 3. Content readiness by folder

### 00 — Administration

| Item | Rating | Repo pointer / upload |
|------|--------|----------------------|
| This checklist | Ready | `docs/acquisition/DATA_ROOM_READINESS.md` |
| VDR index | Ready | `docs/business/Virtual-Data-Room-Index.md` |
| Acquisition strategy | Ready | `docs/acquisition/ACQUISITION_STRATEGY.md` |
| Executive buyer summary | Ready | `docs/acquisition/EXECUTIVE_SUMMARY_FOR_BUYERS.md` |

### 01 — Corporate

| Item | Rating | Notes |
|------|--------|-------|
| Company overview | Ready | `business/company/COMPANY_OVERVIEW.md` |
| Entity registration extracts | Not ready | Pakistan entity — OWNER UPLOAD |
| Cap table / ownership | Not ready | Even founder-only schedule needed |
| Org chart / key persons | Partial | Describe founder-centric reality honestly |
| Board minutes / resolutions | N/A yet or Not ready | Upload if any; else affirmative N/A |
| Related-party / RTAS ecosystem note | Partial | Clarify product vs operator in memo |
| Insurance certificates | Not ready | Or disclose none |

### 02 — Legal

| Item | Rating | Notes |
|------|--------|-------|
| Live Terms / Privacy / Refund / Cookies / AI / Trust & Safety | Ready | https://rtasstudio.com/* + legal sign-off |
| Legal audit / sign-off PDFs | Ready | `docs/LEGAL_*` |
| Paddle compliance narrative | Ready | `docs/PADDLE_COMPLIANCE_REPORT.md` |
| Litigation schedule | Not ready | Affirmative “none” letter acceptable |
| Customer DPA template | Partial | Counsel draft if enterprise buyer |
| Counsel engagement letter | Not ready | OWNER UPLOAD |

### 03 — Financial

| Item | Rating | Notes |
|------|--------|-------|
| Pricing / credits truth | Ready | Verified tiers |
| Illustrative projections | Ready (labeled) | `Financial-Projections.md` |
| Valuation methods memo | Ready (not appraisal) | `Company-Valuation.md` |
| Historical P&L | Not ready | Or state bootstrap / early |
| Bank statements (redacted) | Not ready | OWNER UPLOAD |
| Paddle payout / transaction exports | Not ready | Critical once MoR live |
| GPU / Fal invoices sample | Not ready | For COGS diligence |
| Unit economics model | Partial | Finance folder still thin |

### 04 — Product & commercial

| Item | Rating | Notes |
|------|--------|-------|
| Product one-pager / exec summary | Ready | `docs/sales/*` |
| Pricing page / plan matrix | Ready | Live site |
| ICP / GTM / sales playbooks | Ready | Sprints 1, 4, 8 |
| Customer list / logos | Not ready | No invented logos; upload only real permissioned |
| Pipeline CRM export | Not ready | After CRM stands up |
| MoR status one-pager | Partial | Founder must write weekly factual status |

### 05 — Technical

| Item | Rating | Notes |
|------|--------|-------|
| Architecture | Ready | `docs/ARCHITECTURE.md` |
| Tech DD memo | Ready | `docs/business/Technical-Due-Diligence.md` |
| Known limitations | Ready | `docs/KNOWN_LIMITATIONS.md` |
| Environment / deployment docs | Ready | Ops docs (no secrets) |
| SBOM / license inventory | Partial | Formal SBOM incomplete |
| Source access instructions | Partial | Late diligence only |

### 06 — Security & privacy

| Item | Rating | Notes |
|------|--------|-------|
| Security documentation | Ready | `docs/SECURITY.md` |
| Pre-launch security audit notes | Ready | In repo audits |
| Pen-test report | Not ready | Do not invent; N/A yet if none |
| SOC 2 / ISO certificates | Not ready | Not claimed |
| Access control matrix (admins, DNS, secrets) | Not ready | Founder action — critical for M&A |
| Incident history summary | Partial | Affirmative disclosure if any |

### 07 — Infrastructure & operations

| Item | Rating | Notes |
|------|--------|-------|
| Hosting topology (Vercel, Supabase, Cloudflare, etc.) | Ready | Docs |
| Backup / recovery docs | Ready | Backup/DR docs |
| DR test evidence | Partial | Limited drill evidence |
| Support runbooks / SLAs | Partial | Channels exist; metrics early |
| Domain registrar transfer readiness | Partial | Confirm lock/auth codes process |
| Email continuity (Resend / aliases) | Partial | Documented; full runbook partial |

### 08 — IP & brand

| Item | Rating | Notes |
|------|--------|-------|
| IP inventory memo | Ready | [`IP_AND_INTELLECTUAL_PROPERTY.md`](./IP_AND_INTELLECTUAL_PROPERTY.md) |
| Trademark registrations | Not ready | Do not invent; disclose status honestly |
| Patent filings | N/A yet | None asserted |
| Domain ownership proof | Partial | Registrar screenshot OWNER UPLOAD |
| Contractor IP assignments | Not ready | Critical |
| Open-source policy / notices | Partial | Improve license inventory |

### 09 — People

| Item | Rating | Notes |
|------|--------|-------|
| Contractor / employee roster | Not ready | OWNER UPLOAD |
| Key agreements | Not ready | Counsel |
| Retention / transition plan draft | Partial | Needed for acqui-hire structures |

### 10 — Roadmap & strategy

| Item | Rating | Notes |
|------|--------|-------|
| Business roadmap | Ready | Labeled assumptions |
| Growth scenarios A–E | Ready | [`LONG_TERM_GROWTH_SCENARIOS.md`](./LONG_TERM_GROWTH_SCENARIOS.md) |
| Exit / acquisition strategy | Ready | Sprint 3 + this folder |
| Investor pack | Ready | `docs/investors/*` |

---

## 4. Sharing stages (recommended)

| Stage | What to open | Who |
|-------|--------------|-----|
| Public | Website, legal, pricing | Anyone |
| NDA Tier 1 | Buyer summary, pitch materials, architecture overview | Exploratory parties |
| NDA Tier 2 | Financial illustrative models, risk memos, deeper DD | Serious parties |
| NDA Tier 3 | Corporate extracts, bank/MoR, source guest access | LOI / exclusivity |

Never skip NDA for Tier 2+.

---

## 5. Definition of “data room ready” for a marketed process

All must be true:

1. External VDR live with access log.  
2. Corporate extracts + cap table uploaded.  
3. MoR status one-pager current (≤7 days old).  
4. IP assignment status documented (even if remediation plan).  
5. Admin/secrets access matrix uploaded.  
6. No secrets in shared folders.  
7. Counsel aware of process.

**Current state vs definition:** **Partial** — documentation Ready; uploads and MoR proof lag.

---

## 6. Founder 14-day stand-up plan (real-world)

| Day | Action |
|-----|--------|
| 1–2 | Create external VDR; mirror folder tree |
| 3 | Upload legal PDF exports + company overview |
| 4–5 | Draft cap table + entity extract request |
| 6 | Write MoR status one-pager |
| 7–8 | Build admin/DNS/secrets access matrix |
| 9–10 | Collect domain + email ownership proofs |
| 11–12 | Contractor IP assignment checklist |
| 13 | NDA template from counsel |
| 14 | Dry-run: grant a trusted advisor View access; verify audit log |

---

*Phase 11 Sprint 9 · Overall: **Partial**. Deep index: Sprint 3 `Virtual-Data-Room-Index.md`.*
