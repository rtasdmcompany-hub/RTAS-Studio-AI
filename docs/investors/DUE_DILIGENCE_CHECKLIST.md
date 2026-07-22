# RTAS Studio AI — Due Diligence Checklist

**Classification:** Data-room readiness  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Date:** 22 July 2026 · Phase 11 Sprint 5  

**Instructions:** Mark each item **Ready / Partial / Missing / N/A**. Prefer links to existing repo docs over recreating content. Do not fabricate certificates, customers, or financials to clear a row.

---

## 1. Corporate & entity

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 1.1 | Legal entity documents (registration) | Founder-held | Operator: RTAS Digital Marketing Company |
| 1.2 | Trade names / brand ownership (RTAS Studio AI) | | |
| 1.3 | Cap table / ownership ledger | Counsel | Not invented in repo |
| 1.4 | Material contracts list | | MoR, cloud, domain, contractors |
| 1.5 | Related-party transactions disclosure | | RTAS ecosystem clarity |
| 1.6 | Jurisdiction summary (Pakistan operator + global SaaS) | Partial in docs | Company Overview |

---

## 2. Product & technology

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 2.1 | Architecture overview | Ready | `docs/ARCHITECTURE.md` |
| 2.2 | Engineering freeze / version | Ready | v1.0.0 report |
| 2.3 | Active stack | Ready | `docs/ACTIVE-STACK.md` |
| 2.4 | API documentation | Ready | `docs/API.md` / developer docs |
| 2.5 | Known limitations | Ready | `docs/KNOWN_LIMITATIONS.md` |
| 2.6 | Deployment / production runbooks | Ready | `docs/DEPLOYMENT.md`, `PRODUCTION.md` |
| 2.7 | Backup / recovery | Ready | `docs/BACKUP_RECOVERY.md`, `RECOVERY.md` |
| 2.8 | Environment / secrets handling policy | Ready | `docs/ENVIRONMENT.md` (no secrets in git) |
| 2.9 | Source control access & branch protection | Partial | `docs/GITHUB-BRANCH-PROTECTION.md` |
| 2.10 | Demo account / walkthrough | Founder | Live site rtasstudio.com |

---

## 3. Security & privacy

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 3.1 | Security documentation | Ready | `docs/SECURITY.md` |
| 3.2 | Pre-launch security audit notes | Ready | `docs/FINAL-PRE-LAUNCH-SECURITY-AUDIT.md` |
| 3.3 | Auth model (sessions, reset, admin) | Partial→Ready | Engineering report |
| 3.4 | Webhook signing / fail-closed billing patterns | Documented | Payments docs |
| 3.5 | Privacy Policy (live) | Ready | v1.1 · rtasstudio.com/privacy |
| 3.6 | Cookie Policy | Ready | /cookies |
| 3.7 | Data subprocessors list | Partial | Paddle, Fal, Vercel, Supabase, Resend, Cloudflare — confirm current |
| 3.8 | SOC2 / ISO certificates | Missing / N/A | Do not claim |
| 3.9 | Penetration test report | Missing / optional | |
| 3.10 | Vulnerability disclosure contact | Partial | support@ / security process TBD |

---

## 4. Legal & trust

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 4.1 | Terms of Service | Ready | v1.1 APPROVED |
| 4.2 | Refund Policy | Ready | |
| 4.3 | AI Policy | Ready | /ai-policy |
| 4.4 | Trust & Safety | Ready | /trust-safety |
| 4.5 | Legal sign-off record | Ready | `docs/LEGAL_DOCUMENTATION_SIGNOFF.md` |
| 4.6 | Acceptable Use (Terms §10) | Ready | Paddle AUP-aligned posture |
| 4.7 | IP assignment from contractors | Founder/counsel | |
| 4.8 | Open-source license compliance | Partial | Inventory recommended |
| 4.9 | Trademark filings | Founder | Status as applicable |

---

## 5. Commercial & billing

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 5.1 | Published pricing | Ready | $5 / $89 / $249 · 1 credit = 1s |
| 5.2 | Credit model documentation | Ready | Product/credits docs · shared constants |
| 5.3 | Paddle MoR agreement status | Founder | **Honest gap if checkout pending** |
| 5.4 | Checkout live test evidence | Founder | Screenshot/logs when true |
| 5.5 | Webhook / entitlement reconciliation notes | Documented | `docs/PAYMENTS-WEBHOOKS.md` |
| 5.6 | Refund handling path | Ready | Policy + MoR process |
| 5.7 | Revenue reports (actual) | Missing until live | Do not invent |
| 5.8 | Tax/VAT handling description | Via MoR | Paddle |

---

## 6. Go-to-market & sales

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 6.1 | ICP | Ready | `business/sales/ICP.md` |
| 6.2 | Positioning / USP | Ready | `business/marketing/*` |
| 6.3 | Sales playbook | Ready | `docs/business/sales/Sales-Playbook.md` |
| 6.4 | GTM strategy | Ready | `Go-To-Market-Strategy.md` |
| 6.5 | Enterprise process + proposal + demo | Ready | Sprint 4 pack |
| 6.6 | CRM implementation evidence | Partial | Workflow documented; tool may be pending |
| 6.7 | Pipeline report (real) | Missing until run | |
| 6.8 | Customer logos / case studies | Missing | **None invented** |

---

## 7. Market & competition

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 7.1 | Market analysis with citations | Ready | `business/marketing/MARKET_ANALYSIS.md` |
| 7.2 | Competitor matrix | Ready | `COMPETITOR_MATRIX.md` |
| 7.3 | Sales competitive analysis | Ready | `docs/sales/Competitive-Analysis.md` |
| 7.4 | SWOT | Ready | `business/company/SWOT.md` |

---

## 8. Financials

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 8.1 | Historical P&L / balance sheet | Founder | Not in this pack |
| 8.2 | Bank statements | Founder / NDA | |
| 8.3 | Burn & runway model | Partial | Use of Funds = hypothetical |
| 8.4 | Unit economics with COGS/sec | Partial | Needs Fal telemetry |
| 8.5 | Metrics handbook (definitions) | Ready | `docs/sales/Business-Metrics.md` |
| 8.6 | Roadmap scenario bands | Ready | Labeled ASSUMPTION |
| 8.7 | Prior financing documents | N/A or founder | No invented rounds |

---

## 9. People & HR

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 9.1 | Org chart (current) | Founder | Honest small-team |
| 9.2 | Hiring roadmap | Ready | `TEAM_ROADMAP.md` |
| 9.3 | Contractor agreements / IP | Counsel | |
| 9.4 | Compensation summary | Founder / NDA | |
| 9.5 | Key-person continuity plan | Partial | Playbooks + hiring plan |

---

## 10. Investor materials

| # | Item | Status guide | Notes / location |
|---|------|--------------|------------------|
| 10.1 | Investor memorandum | Ready | `INVESTOR_MEMORANDUM.md` |
| 10.2 | Pitch deck content (18 slides) | Ready | `PITCH_DECK_CONTENT.md` |
| 10.3 | Designed PDF/PPT deck | Partial | Content ready; design export TBD |
| 10.4 | Fundraising strategy | Ready | `FUNDRAISING_STRATEGY.md` |
| 10.5 | Use of funds | Ready | Labeled hypothetical |
| 10.6 | Investor Q&A | Ready | `INVESTOR_QA.md` |
| 10.7 | Founder playbook | Ready | `FOUNDER_PLAYBOOK.md` |
| 10.8 | Board meeting template | Ready | `BOARD_MEETING_TEMPLATE.md` |
| 10.9 | Sprint 1–5 business reports | Ready | See cross-links below |
| 10.10 | Sales kit (Sprint 2) | Ready | `docs/sales/*` |

---

## 11. Vendor & dependency register

| Vendor / dependency | Role | Diligence note |
|---------------------|------|----------------|
| **Paddle** | Merchant of Record | Agreement status; checkout activation; AUP history |
| **Fal** | GPU / model inference | Account, wallet, model ToS, COGS |
| **Vercel** | Web hosting | Plan, domains, logs retention |
| **Supabase** | Postgres / auth-related infra | Data region, backups, access |
| **Resend** | Transactional email | Domain auth (SPF/DKIM/DMARC) |
| **Cloudflare** | DNS / edge | Zone ownership, email routing if any |
| **GitHub** | Source control | Access control, protection rules |
| **Google OAuth** (if enabled) | Auth provider | Client config; secret hygiene |
| **Domain registrar** | rtasstudio.com | Ownership proof |
| **Open-source libs** | App dependencies | License scan recommended |

---

## 12. Red-flag self-audit (founders)

| Red flag | Mitigation |
|----------|------------|
| Invented traction in deck | Remove; use Traction honesty slide |
| MoR status contradicted across docs | Single weekly status sentence |
| Deepfake-adjacent marketing drift | Re-check Trust & Safety copy |
| Secrets in git | Rotate + remove |
| Overclaiming SOC2/SSO | Downgrade language to roadmap |
| Stale pricing vs product | Align to $5 / $89 / $249 |

---

## 13. Cross-links — Phase 11 reports

| Sprint | Report |
|--------|--------|
| 1 | [`business/PHASE11_SPRINT1_REPORT.md`](../../business/PHASE11_SPRINT1_REPORT.md) |
| 2 | [`docs/business/PHASE11-SPRINT2-REPORT.md`](../business/PHASE11-SPRINT2-REPORT.md) |
| 4 | [`docs/business/PHASE11-SPRINT4-REPORT.md`](../business/PHASE11-SPRINT4-REPORT.md) |
| 5 | [`docs/business/PHASE11-SPRINT5-REPORT.md`](../business/PHASE11-SPRINT5-REPORT.md) |

---

## 14. Suggested data-room folder map (external share)

```text
00_Index/
01_Corporate/
02_Legal_Trust/
03_Product_Engineering/
04_Security_Privacy/
05_Commercial_Billing/
06_GTM_Sales/
07_Financials/          (founder-populated)
08_People/
09_Investor_Materials/  (this docs/investors pack)
10_Vendor_Contracts/
```

---

*Checklist complete when Ready/Partial/Missing is honestly marked—not when every row is green by fiction.*
