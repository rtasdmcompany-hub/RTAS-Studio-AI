# Security Governance — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Status:** Implemented baseline controls (documented); **not** ISO 27001 / SOC 2 certified  

**Related:** [docs/SECURITY.md](../SECURITY.md) · [docs/FINAL-PRE-LAUNCH-SECURITY-AUDIT.md](../FINAL-PRE-LAUNCH-SECURITY-AUDIT.md) · [docs/ENVIRONMENT.md](../ENVIRONMENT.md) · [docs/GITHUB-BRANCH-PROTECTION.md](../GITHUB-BRANCH-PROTECTION.md) · [CHANGE_MANAGEMENT.md](./CHANGE_MANAGEMENT.md) · [COMPLIANCE_REGISTER.md](./COMPLIANCE_REGISTER.md)

---

## 1. Governance principles

1. **No secrets in git.**  
2. **Fail closed** in production when auth, payment webhooks, or critical config are missing.  
3. **Least privilege** for humans and service roles.  
4. **Merchant of Record:** card data stays with Paddle; RTAS does not store PANs.  
5. **Honest claims:** describe controls as implemented; do not claim unearned certifications.  
6. **Rotate on exposure** — any key pastedin chat, email, or screenshots is compromised.

---

## 2. Access control

| Surface | Control (implemented / goal) |
|---------|------------------------------|
| Production app admin APIs | `RTAS_ADMIN_SECRET` required in production (**implemented**) |
| Owner email UI affordance | `NEXT_PUBLIC_OWNER_EMAILS` is **not** authorization (**implemented caveat**) |
| Vercel / Supabase / Cloudflare / Paddle / Fal / Resend / GitHub / Google Cloud / Forward Email / Hostinger | Operator accounts with MFA **goal: enforced on all**; verify monthly |
| Customer accounts | NextAuth credentials + Google OAuth; session-protected `/studio`, `/profile` (**implemented**) |
| Database service role | Server-only; never `NEXT_PUBLIC_*` (**implemented policy**) |

**Access review cadence:** Monthly lightweight · Quarterly full attestation of privileged users.

**Joiners/movers/leavers:** Founder-operated today — on any contractor engagement, provision least privilege and revoke on exit same day.

---

## 3. Password & authentication policy

| Topic | Rule |
|-------|------|
| Operator passwords | Unique, password manager; never shared in plaintext |
| MFA | Required goal for all vendor consoles with production impact |
| Customer passwords | Hashed via auth stack; reset tokens HMAC-signed, short TTL, rate-limited (**implemented** per security docs) |
| Google OAuth | Production redirects/origins limited to intended domains; `allowDangerousEmailAccountLinking: false` |
| Session invalidation | Rotate `NEXTAUTH_SECRET` to force re-login after major compromise |

---

## 4. Secrets management

| Do | Do not |
|----|--------|
| Store in Vercel Environment Variables + local `.env.local` (gitignored) | Commit `.env.local`, `.env`, credentials JSON |
| Use `.env.production.example` placeholders | Hardcode keys in source |
| Scope GitHub PATs minimally | Put service-role keys in client bundles |
| Rotate after leak or staff change | Share secrets in Discord/Slack unencrypted |

Generate strong secrets with a CSPRNG (e.g. `openssl rand -base64 32`).

**Inventory (names only — no values):** NEXTAUTH_SECRET, database URLs, Google client secret, Resend API key, Paddle webhook secret / API credentials, Fal key, RTAS_ADMIN_SECRET, any KV tokens.

---

## 5. Environment governance

| Environment | Purpose | Rules |
|-------------|---------|-------|
| Local | Development | `.env.local`; never production webhook secrets in shared chat |
| Preview | PR validation | Separate Vercel env where possible; no production data dumps |
| Production | rtasstudio.com | Change via [CHANGE_MANAGEMENT.md](./CHANGE_MANAGEMENT.md); smoke after env edits |

Env drift check: monthly compare critical keys’ **presence** (not values) against `apps/web/.env.production.example`.

---

## 6. Repository & supply chain

| Control | Status |
|---------|--------|
| Secrets gitignored | Implemented |
| Lockfile / CI install | Implemented |
| Branch protection | Documented in `docs/GITHUB-BRANCH-PROTECTION.md` — enforce as configured |
| `npm audit` | Weekly/monthly ops cadence |
| Dependency upgrades for known Next CVEs | Track residual risk until upgraded (see security docs) |
| No commit of `node_modules` or secret-bearing artifacts | Policy |

---

## 7. Application security controls (summary)

Documented in depth in [docs/SECURITY.md](../SECURITY.md):

- Paddle webhook HMAC verification; fail closed if secret missing in production  
- Session/auth helpers on generate, checkout, trial, notify paths  
- Path traversal hardening on compile paths  
- Rate limiting (in-memory; Redis/KV when linked — upgrade for multi-instance)  
- Security headers: HSTS, frame deny, nosniff, referrer policy, permissions policy  
- TLS to Postgres (`sslmode=require` recommended); RLS for client-exposed tables  

---

## 8. Audit & logging

| Source | Use |
|--------|-----|
| Vercel runtime / deploy logs | Incident forensics |
| Observability helpers | Structured events (`docs/OPERATIONS.md`) |
| Supabase / GitHub audit | Access anomalies |
| Paddle dashboard | Payment/webhook anomalies |
| Resend | Bounce/complaint abuse signals |

**Goal (not claimed live everywhere):** centralized SIEM / Sentry when `NEXT_PUBLIC_SENTRY_DSN` (or equivalent) is wired.

**Retention:** follow vendor defaults unless a customer contract requires more; do not claim multi-year forensic retention without configuration proof.

---

## 9. Security review calendar

| Review | Cadence |
|--------|---------|
| Access & MFA spot-check | Monthly |
| Secret presence / rotation triggers | Monthly |
| Dependency advisories | Weekly ops · Monthly remediation planning |
| Full security governance re-read | Quarterly |
| External penetration test / SOC 2 readiness | **Goal** — not scheduled as certified program |
| Pre-launch style audit refresh | After major auth/payment changes |

---

## 10. Incident authority

Ops Owner declares security incidents (SOP-06). Prefer containment over perfect root cause in the first hour. Customer notices: factual, no overclaim.

---

## 11. Statements for enterprise questionnaires

| Question type | Answer posture |
|---------------|----------------|
| “Are you SOC 2 certified?” | **No** (goal/future if pursued) |
| “ISO 27001?” | **No** |
| “GDPR certified?” | **No** — privacy policy and MoR disclosures exist; certification is not claimed |
| “Do you store card data?” | **No** — Paddle MoR |
| “Encryption in transit?” | TLS via Vercel/Supabase as configured |
| “Employee background checks / SSO / SCIM?” | Not offered as standard today |

**Owner:** Ops Owner · **Review:** Quarterly · **Phase 11 Sprint 6**
