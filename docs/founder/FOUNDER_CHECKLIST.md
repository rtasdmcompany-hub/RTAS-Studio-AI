# Founder Checklist — RTAS Studio AI

**Operator:** RTAS Digital Marketing Company  
**Product:** https://rtasstudio.com  
**Phase:** 13 · Sprint 10  
**As-of:** 23 July 2026  

Use as a living checklist. Mark dates; attach evidence links. Do not tick Critical commercial items without proof.

---

## Daily

| # | Task | Pass criteria | Owner |
|---|------|---------------|-------|
| D1 | `GET /api/health` | `status: ok` | Founder |
| D2 | `GET /api/ready` | `status: ready` (alert on 503) | Founder |
| D3 | Vercel production deploy / runtime errors | No unexplained spike | Founder |
| D4 | Support inbox (`support@` / `contact@`) | SEV≥2 acknowledged | Founder |
| D5 | Fal / generation runway (when live) | Balance not near zero | Founder |
| D6 | Paddle dashboard (when checkout live) | No silent webhook failure pile-up | Founder |
| D7 | Resend (bounces/complaints) | No sudden spike | Founder |
| D8 | One-line daily log | Date · health · ready · incidents · notes | Founder |

---

## Weekly

| # | Task | Pass criteria |
|---|------|---------------|
| W1 | Auth smoke (login + forgot-password UI) | Pages load; spot inbox receipt when testing |
| W2 | Pricing truth spot-check | `/pricing` still shows $5 / $89 / $249 |
| W3 | Credit ledger sanity (if any paid users) | Grants match MoR events |
| W4 | Dependency / security glance | High-severity npm advisories triaged |
| W5 | Change review | List prod deploys vs intent |
| W6 | Pipeline / CRM honesty | Only real leads; no invented stages filled |
| W7 | Metrics sheet | Fill actuals or leave blank — never invent |
| W8 | Status page honesty | Do not claim “all operational” if Fal/billing known down |

---

## Monthly

| # | Task | Pass criteria |
|---|------|---------------|
| M1 | Access review | GitHub / Vercel / Supabase / Cloudflare / admin emails |
| M2 | Secret hygiene | No secrets in git; rotate if exposure risk |
| M3 | Backup / restore drill | Per [`../BACKUP_RECOVERY.md`](../BACKUP_RECOVERY.md) — document result |
| M4 | Vendor invoices | Vercel, Supabase, Fal, Resend, Cloudflare, MoR fees |
| M5 | Legal page spot-check | Terms/Privacy/Refund still accurate vs product |
| M6 | Risk register refresh | Update [`../release/LAUNCH_RISK_REGISTER.md`](../release/LAUNCH_RISK_REGISTER.md) |
| M7 | Affiliate / partner claims audit | No unpublished partners listed as live |

---

## Security review (monthly minimum; after any incident)

| # | Check |
|---|-------|
| S1 | AuthZ still fail-closed on `/api/generate` and `/api/checkout` (unauth → 401) |
| S2 | Webhooks reject unsigned payloads |
| S3 | Admin routes gated |
| S4 | CSP / headers drift review |
| S5 | Abuse / AUP reports triaged |
| S6 | Prior audit: [`../FINAL-PRE-LAUNCH-SECURITY-AUDIT.md`](../FINAL-PRE-LAUNCH-SECURITY-AUDIT.md) |

---

## Revenue review (weekly when commercial live; otherwise gate review)

| # | Check |
|---|-------|
| R1 | MoR transactions vs ledger (no silent misses) |
| R2 | Failed payments / dunning |
| R3 | Refunds & chargebacks |
| R4 | Plan mix: Tester / Standard / Premium (real counts only) |
| R5 | Gross vs net after MoR fees (finance sheet) |
| R6 | **Until C1 cleared:** paid ads spend = **$0** |

---

## Customer / support review (weekly)

| # | Check |
|---|-------|
| CS1 | Open tickets by severity |
| CS2 | Time-to-first-response |
| CS3 | Recurring product bugs → backlog |
| CS4 | Feedback form / mailto themes |
| CS5 | Discord invite still valid (or remove) |

---

## Backup & continuity (monthly)

| # | Check |
|---|-------|
| B1 | Supabase backup / PITR posture confirmed |
| B2 | Env/secrets export discipline (not in git) |
| B3 | DNS zone doc still accurate [`../RTASSTUDIO-COM-DNS.md`](../RTASSTUDIO-COM-DNS.md) |
| B4 | Rollback path known ([`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md)) |

---

## Incident review (after each SEV-1/2; monthly tabletop)

| # | Check |
|---|-------|
| I1 | Timeline written |
| I2 | Customer comms honest |
| I3 | Root cause + fix |
| I4 | Preventive action dated |
| I5 | Update BCP if playbook wrong |

---

## Product review (bi-weekly)

| # | Check |
|---|-------|
| P1 | Roadmap honesty ([`VERSION_ROADMAP.md`](./VERSION_ROADMAP.md)) |
| P2 | Naming consistency (Tester/Standard/Premium vs marketing labels) |
| P3 | Free-trial / watermark copy vs paid Tester truth |
| P4 | Identity Preservation authorized-only language intact |
| P5 | Critical bugs vs polish backlog |

---

## Pre–paid-ads gate (all must be Cleared)

- [ ] C1 Live Tester purchase → credits evidenced  
- [ ] C2 Live generation evidenced  
- [ ] Webhook + price IDs confirmed  
- [ ] Support path (`/help/contact` and preferably `/contact`) works  
- [ ] Sitemap 200  
- [ ] Observability on or written deferral  

---

*Phase 13 Sprint 10 — Founder Checklist.*
