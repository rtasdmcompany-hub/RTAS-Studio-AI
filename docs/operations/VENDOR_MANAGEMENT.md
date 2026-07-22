# Vendor Management — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Security rule:** This document contains **no API keys, passwords, tokens, or webhook secrets**.

**Related:** [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md) · [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) · [RISK_REGISTER.md](./RISK_REGISTER.md) · [docs/ACTIVE-STACK.md](../ACTIVE-STACK.md) · [docs/INFRASTRUCTURE.md](../INFRASTRUCTURE.md)

---

## 1. Purpose

Inventory third-party dependencies that keep RTAS Studio AI commercially operable: hosting, data, AI, email, payments, DNS history, identity, and source control. Use this register for quarterly reviews, onboarding diligence answers, and incident fallback decisions.

---

## 2. Vendor register

| Vendor | Function | Criticality | Data involved (high level) | Fallback / mitigation | Key risks | Review cadence |
|--------|----------|-------------|----------------------------|------------------------|-----------|----------------|
| **Vercel** | Web hosting, serverless, env, SSL for app | **Critical** | App logs, env config (secrets in dashboard) | Promote prior deployment; limited alternate host (migration effort) | Platform outage; misconfigured env | Quarterly + after outages |
| **Cloudflare** | DNS / edge for domain path | **Critical** | DNS records; traffic metadata | Re-point nameservers / restore documented zone | Mis-edit DNS; TTL delay | Quarterly + after DNS changes |
| **Supabase** | Postgres database | **Critical** | Accounts, credits, app data | Backups/PITR (plan-dependent); restore drill | Data loss; credential leak; plan limits | Monthly health · Quarterly strategic |
| **Fal.ai** | Primary AI video generation | **Critical** | Prompts, media artifacts, usage | Optional Replicate if configured; degrade generation UX | Cost spikes; outage; AUP enforcement | Weekly balance · Quarterly contract/ToS |
| **Resend** | Transactional email | **High** | Email addresses, message metadata | SMTP alternate if configured; manual support contact | Deliverability; domain auth break | Monthly · Quarterly |
| **Paddle** | Merchant of Record (payments, tax, refunds) | **Critical** (when checkout live) | Billing identity, MoR transaction data (no PAN in RTAS systems) | No second MoR live; Lemon path may exist in codebase history — commercial default is Paddle | **Checkout/domain approval may be pending**; AUP rejection; webhook failure | Weekly while gated · Monthly when live |
| **Hostinger** | Domain registration history / prior DNS | **Medium** | Registrar account | Cloudflare/Vercel DNS as active path; keep registrar access | Lost registrar access; expiry | Semi-annual |
| **GitHub** | Source control, CI | **Critical** | Source, Actions logs | Local clones; Vercel prior artifacts | Account compromise; CI supply chain | Quarterly access review |
| **Google OAuth** | Social login | **High** | OAuth identity assertions | Credentials login / email verification path | Console misconfig; redirect mismatch | Monthly smoke · Quarterly console review |
| **Forward Email** | Inbound alias routing for @rtasstudio.com | **Medium–High** | Inbound mail routing | Direct mailbox / temporary public alternate | Routing misconfig; vendor outage | Monthly · after DNS changes |

**Optional / secondary (document if enabled):** Replicate (AI fallback), Vercel KV/Upstash (rate-limit/state), analytics vendors if `NEXT_PUBLIC_*` analytics IDs enabled, Sentry if DSN configured.

---

## 3. Criticality definitions

| Level | Meaning |
|-------|---------|
| Critical | Outage blocks core revenue or core product within hours |
| High | Severe degradation; workarounds partial |
| Medium | Operational friction; core product may continue |
| Low | Convenience / future |

---

## 4. Vendor onboarding checklist (new vendor)

1. Business justification and data classification.  
2. Confirm no PAN storage requirement (payments stay with MoR).  
3. Least-privilege account; MFA on operator login.  
4. Secrets only in Vercel/vault — never git.  
5. Add to this register + Risk Register.  
6. Document fallback before production cutover.  
7. Legal/ToS skim for AUP conflicts with Trust & Safety / AI Policy.

---

## 5. Vendor offboarding checklist

1. Disable integrations and webhooks.  
2. Rotate related secrets.  
3. Export data if needed; confirm deletion where required.  
4. Update DNS/docs and this register.  
5. Announce customer impact if any.

---

## 6. Performance & commercial review questions

- Is spend proportional to usage (especially Fal and Vercel)?  
- Any ToS/AUP change affecting generative video or MoR?  
- Is Paddle checkout **approved and reliable** for rtasstudio.com this period? (Honest answer required.)  
- Backup/PITR tier still adequate for RPO goals?  
- Single-person access risk on registrar or MoR?

---

## 7. Concentration risk (honest)

RTAS Studio AI is **cloud-concentrated**: Vercel + Supabase + Fal + Paddle. This is appropriate for Stage-appropriate speed and cost. It is **not** a dual-vendor active-active enterprise architecture. Mitigations are backups, rollback, documented DNS, and optional AI fallback — not full hot replicas of every tier.

---

## 8. Diligence language (allowed)

**Allowed:** “We use reputable cloud vendors (Vercel, Supabase, Fal.ai, Resend, Paddle as MoR) with operator security practices documented in our governance pack.”  

**Not allowed:** Claiming ISO/SOC2/GDPR **certification** for RTAS or implying vendors’ certifications automatically transfer to RTAS without a customer DPA/attestation package.

**Owner:** Ops Owner · **Review:** Quarterly · **Phase 11 Sprint 6**
