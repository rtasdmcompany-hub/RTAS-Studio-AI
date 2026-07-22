# RTAS Studio AI — Virtual Data Room (VDR) Index

**Classification:** Confidential — M&A / Investment diligence  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Phase:** 11 · Sprint 3  
**Purpose:** Index of folders an acquirer or investor should expect. Items marked **IN REPO** exist as documentation or code pointers; items marked **OWNER UPLOAD** must be added as PDFs/exports outside public git when a live process opens.

**Honesty:** Early-stage. Do not place secrets, PANs, or live credentials in git. Use a secured VDR (e.g., Google Drive / Dropbox / dedicated DD room) mirroring this index.

---

## How to use this index

| Tag | Meaning |
|-----|---------|
| **IN REPO** | Present in this repository as docs/code (path given) |
| **PARTIAL** | Some materials exist; gaps remain |
| **OWNER UPLOAD** | Required for live diligence; not asserted as complete in git |
| **N/A YET** | Not applicable until traction/entity milestones occur |

---

## 00 — VDR Administration

| Document | Status | Location / action |
|----------|--------|-------------------|
| NDA template | OWNER UPLOAD | Counsel-provided |
| Access log / permission matrix | OWNER UPLOAD | Who viewed what |
| Document version control policy | PARTIAL | Prefer dated exports + this index |
| Sprint 3 pack map | IN REPO | `docs/business/*` |

---

## 01 — Corporate

| Document | Status | Location / action |
|----------|--------|-------------------|
| Company overview | IN REPO | `/business/company/COMPANY_OVERVIEW.md` |
| Product positioning | IN REPO | `/business/company/PRODUCT_POSITIONING.md`, `/business/marketing/PRODUCT_POSITIONING.md` |
| SWOT / USP | IN REPO | `/business/company/SWOT.md`, `/business/company/USP.md` |
| Certificate of incorporation / registration | OWNER UPLOAD | Pakistan entity extracts |
| Constitutional documents / bylaws | OWNER UPLOAD | |
| Cap table & fully diluted schedule | OWNER UPLOAD | |
| Org chart / key persons | OWNER UPLOAD | Include founder dependency note |
| Board consents / resolutions | OWNER UPLOAD | Or N/A YET if none |
| Related-party transactions schedule | OWNER UPLOAD | RTAS ecosystem clarity |
| Insurance certificates | OWNER UPLOAD | Or disclose none |

---

## 02 — Legal

| Document | Status | Location / action |
|----------|--------|-------------------|
| Terms of Service (live) | IN REPO / LIVE | Site + `packages/shared` legal modules |
| Privacy Policy | IN REPO / LIVE | |
| Refund Policy | IN REPO / LIVE | |
| Cookie Policy | IN REPO / LIVE | |
| AI Usage Policy | IN REPO / LIVE | |
| Trust & Safety | IN REPO / LIVE | |
| Legal sign-off / audit | IN REPO | `docs/LEGAL_DOCUMENTATION_SIGNOFF.md`, `docs/LEGAL_POLICY_AUDIT_v1.1.md` |
| Paddle compliance report | IN REPO | `docs/PADDLE_COMPLIANCE_REPORT.md` |
| Legal index | IN REPO | `/business/legal/README.md` |
| Litigation schedule | OWNER UPLOAD | Affirmative “none” letter acceptable |
| Customer DPA template | OWNER UPLOAD / PARTIAL | |
| Counsel engagement letters | OWNER UPLOAD | |

---

## 03 — Financial

| Document | Status | Location / action |
|----------|--------|-------------------|
| Pricing / credit source of truth | IN REPO | `packages/shared` + product docs |
| Illustrative financial projections | IN REPO | `docs/business/Financial-Projections.md` |
| Company valuation methods | IN REPO | `docs/business/Company-Valuation.md` |
| Roadmap scenario bands | IN REPO | `/business/roadmap/BUSINESS_ROADMAP.md` |
| Historical P&L / balance sheet | OWNER UPLOAD | Or state early-stage / bootstrap |
| Bank statements (redacted) | OWNER UPLOAD | |
| Paddle settlement reports | OWNER UPLOAD | When live |
| Fal.ai / GPU cost exports | OWNER UPLOAD | COGS diligence |
| Tax filings | OWNER UPLOAD | Jurisdiction-appropriate |
| Budget vs actual | OWNER UPLOAD | N/A YET if none |

---

## 04 — Product

| Document | Status | Location / action |
|----------|--------|-------------------|
| Product readiness / commercial reports | IN REPO | `docs/PRODUCT-READINESS-REPORT.md`, `docs/COMMERCIAL-READINESS-REPORT.md` |
| Credits & billing guide | IN REPO | `docs/product/credits-and-billing.md` |
| Studio / FAQ / onboarding | IN REPO | `docs/product/*` |
| Feature marketing specs | IN REPO | `docs/marketing/*` |
| Known limitations | IN REPO | `docs/KNOWN_LIMITATIONS.md` |
| Release notes / version history | IN REPO | `docs/RELEASE_NOTES.md`, `docs/VERSION-HISTORY.md` |
| Product demo recording | OWNER UPLOAD | Optional walkthrough video |
| Roadmap (product) | PARTIAL | Align with business roadmap; avoid fake commitment dates |

---

## 05 — Technical

| Document | Status | Location / action |
|----------|--------|-------------------|
| Architecture | IN REPO | `docs/ARCHITECTURE.md` |
| Active stack | IN REPO | `docs/ACTIVE-STACK.md` |
| API docs | IN REPO | `docs/API.md`, `docs/developer/*` |
| Deployment / production | IN REPO | `docs/DEPLOYMENT.md`, `docs/PRODUCTION.md`, `docs/VERCEL-DEPLOY.md` |
| Infrastructure | IN REPO | `docs/INFRASTRUCTURE.md` |
| Environment variable map (no secrets) | IN REPO | `docs/ENVIRONMENT.md`, `.env.example` files |
| Technical due diligence memo | IN REPO | `docs/business/Technical-Due-Diligence.md` |
| Source code access | IN REPO | Grant read access to `apps/*`, `packages/*` under NDA |
| Dependency / SBOM export | OWNER UPLOAD | Generate at diligence kickoff |
| CI configuration | IN REPO | `.github` workflows if present |

---

## 06 — Security

| Document | Status | Location / action |
|----------|--------|-------------------|
| Security baseline | IN REPO | `docs/SECURITY.md` |
| Pre-launch security audit | IN REPO | `docs/FINAL-PRE-LAUNCH-SECURITY-AUDIT.md` |
| Enterprise audit report | IN REPO | `docs/FINAL-ENTERPRISE-AUDIT-REPORT.md` |
| Auth & webhook controls summary | IN REPO | Security + payments docs |
| Penetration test | OWNER UPLOAD | Or disclose none |
| Vulnerability scan exports | OWNER UPLOAD | |
| Incident response plan | PARTIAL / OWNER UPLOAD | Formalize from ops docs |
| Access control matrix | OWNER UPLOAD | Critical |

---

## 07 — Infrastructure & Operations

| Document | Status | Location / action |
|----------|--------|-------------------|
| Operations guide | IN REPO | `docs/OPERATIONS.md` |
| Backup & recovery | IN REPO | `docs/BACKUP.md`, `docs/BACKUP_RECOVERY.md`, `docs/RECOVERY.md` |
| DNS runbooks | IN REPO | `docs/RTASSTUDIO-COM-DNS.md` |
| Email ops notes | IN REPO | `docs/EMAIL_GMAIL_REPLY_AS_ALIAS.md` |
| Monitoring / status approach | PARTIAL | Admin + status surfaces |
| Vendor list (Vercel, Supabase, Cloudflare, Fal, Paddle, Resend, Google OAuth) | OWNER UPLOAD | With account owners |
| Cost run-rate by vendor | OWNER UPLOAD | |

---

## 08 — Payments & Commerce

| Document | Status | Location / action |
|----------|--------|-------------------|
| Payments / webhooks | IN REPO | `docs/PAYMENTS-WEBHOOKS.md` |
| Commercial readiness | IN REPO | `docs/launch/COMMERCIAL-READINESS.md`, `docs/COMMERCIAL-READINESS-REPORT.md` |
| Paddle compliance & resubmission narrative | IN REPO | `docs/PADDLE_COMPLIANCE_REPORT.md`, `docs/PADDLE_RESUBMISSION_EMAIL.md` |
| Live checkout status attestation | OWNER UPLOAD | **Business gap if pending** |
| Price book PDF | OWNER UPLOAD | Export from verified tiers |
| Refund log | OWNER UPLOAD | When volume exists |

---

## 09 — Customers, Sales & GTM

| Document | Status | Location / action |
|----------|--------|-------------------|
| ICP | IN REPO | `/business/sales/ICP.md` |
| Sales playbook / GTM / CRM / KPI | IN REPO | `docs/business/sales/*` |
| Executive sales summary | IN REPO | `docs/sales/Executive-Summary.md` |
| Sales one-pager | IN REPO | `docs/launch/SALES-ONE-PAGER.md` |
| Customer list / cohort metrics | OWNER UPLOAD | **Do not invent**; upload only verified |
| Pipeline CRM export | OWNER UPLOAD | When CRM used |
| Case studies | OWNER UPLOAD | Only with permission; no fake logos |
| Churn / NRR workbook | OWNER UPLOAD | When ARR exists |

---

## 10 — Marketing & Brand

| Document | Status | Location / action |
|----------|--------|-------------------|
| Market analysis | IN REPO | `/business/marketing/MARKET_ANALYSIS.md` |
| Competitor matrix | IN REPO | `/business/marketing/COMPETITOR_MATRIX.md` |
| Positioning / USP | IN REPO | `/business/marketing/*` |
| Landing / pricing strategy docs | IN REPO | `docs/marketing/*`, `docs/business/PHASE-*-*.md` |
| Brand kit | PARTIAL | `/business/branding/` |
| Domain & social handle inventory | OWNER UPLOAD | |
| Ad account access notes | OWNER UPLOAD | If any |

---

## 11 — Compliance & Trust

| Document | Status | Location / action |
|----------|--------|-------------------|
| Trust & Safety + AI Policy | LIVE + IN REPO | |
| AUP alignment memo | IN REPO | Paddle compliance docs |
| Risk assessment | IN REPO | `docs/business/Risk-Assessment.md` |
| Content moderation SOP | OWNER UPLOAD | Expand from Trust & Safety |
| Privacy / DSR request log | OWNER UPLOAD | |

---

## 12 — Intellectual Property

| Document | Status | Location / action |
|----------|--------|-------------------|
| Source code ownership assertion | PARTIAL | Counsel letter OWNER UPLOAD |
| Employee / contractor IP assignment | OWNER UPLOAD | |
| Trademark filings | OWNER UPLOAD | Or disclose none |
| Patent filings | N/A YET / OWNER UPLOAD | Do not claim if none |
| Open-source license notices | PARTIAL | Generate NOTICE/SBOM |
| Third-party API terms (Fal, Paddle, etc.) | OWNER UPLOAD | Links + acceptance dates |
| Showcase / media asset licenses | OWNER UPLOAD | `apps/web/public/showcase` provenance |

---

## 13 — People & Support

| Document | Status | Location / action |
|----------|--------|-------------------|
| Support channels doc | IN REPO | `docs/product/support-channels.md` |
| Help center pages | LIVE | `/help`, troubleshooting, changelog |
| Contractor agreements | OWNER UPLOAD | |
| Payroll / benefits (if any) | OWNER UPLOAD | |
| Key-person continuity plan | OWNER UPLOAD | Ties to BCP |

---

## 14 — Domain, Email & Analytics

| Document | Status | Location / action |
|----------|--------|-------------------|
| Domain DNS documentation | IN REPO | DNS docs |
| Registrar details | OWNER UPLOAD | Auth code process |
| Email provider configs (no secrets) | PARTIAL | Resend docs/scripts |
| Analytics properties list | OWNER UPLOAD | GA/Search Console/etc. |
| SEO audit notes | PARTIAL | Scripts/docs as available |

---

## 15 — Disaster Recovery & Business Continuity

| Document | Status | Location / action |
|----------|--------|-------------------|
| Backup/recovery docs | IN REPO | Backup/recovery set |
| DR test evidence | OWNER UPLOAD | Restore screenshots/logs |
| BCP / crisis comms | OWNER UPLOAD | |
| RTO/RPO definitions | OWNER UPLOAD | |

---

## 16 — Roadmap

| Document | Status | Location / action |
|----------|--------|-------------------|
| Business roadmap 2026–2028 | IN REPO | `/business/roadmap/BUSINESS_ROADMAP.md` |
| Exit strategy options | IN REPO | `docs/business/Exit-Strategy.md` |
| Acquirer target list | IN REPO | `docs/business/Acquirer-Target-List.md` |
| Engineering backlog (sanitized) | OWNER UPLOAD | From issue tracker; no secrets |
| Investment use-of-funds (illustrative) | PARTIAL | Investor summary narrative |

---

## 17 — Transaction (when process live)

| Document | Status | Location / action |
|----------|--------|-------------------|
| Teaser / CIM | OWNER UPLOAD | Facts-only; no fake traction |
| Valuation memo | IN REPO | `Company-Valuation.md` |
| Acquisition readiness checklist | IN REPO | `Acquisition-Readiness-Checklist.md` |
| Business & technical DD memos | IN REPO | This sprint |
| Letter of intent drafts | OWNER UPLOAD | Counsel |
| Disclosure schedules | OWNER UPLOAD | |

---

## Suggested folder tree (external VDR)

```text
RTAS-Studio-AI-VDR/
├── 00-Admin/
├── 01-Corporate/
├── 02-Legal/
├── 03-Financial/
├── 04-Product/
├── 05-Technical/
├── 06-Security/
├── 07-Infrastructure-Operations/
├── 08-Payments-Commerce/
├── 09-Customers-Sales-GTM/
├── 10-Marketing-Brand/
├── 11-Compliance-Trust/
├── 12-Intellectual-Property/
├── 13-People-Support/
├── 14-Domain-Email-Analytics/
├── 15-DR-BCP/
├── 16-Roadmap/
└── 17-Transaction/
```

---

## Curator checklist before inviting buyers

1. Strip secrets; rotate any previously exposed keys.  
2. Upload entity, IP assignment, and access matrix first.  
3. Attest Paddle live status accurately.  
4. Separate **verified metrics** from **illustrative projections**.  
5. Keep this index as the table of contents; update dates on each upload.

*Companion: `Acquisition-Readiness-Checklist.md`, `PHASE11-SPRINT3-REPORT.md`.*
