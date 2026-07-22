# Standard Operating Procedures — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Related:** [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md) · [SUPPORT_OPERATIONS.md](./SUPPORT_OPERATIONS.md) · [CHANGE_MANAGEMENT.md](./CHANGE_MANAGEMENT.md) · [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md)

---

## How to use this document

Each SOP is a repeatable checklist. Mark outcomes in the daily/weekly ops log. Do not paste API keys, passwords, or webhook secrets into tickets or chat.

---

## SOP-01 — Customer support intake

**Trigger:** Email to support@ or contact@rtasstudio.com, Help/Contact form, or Feedback mailto.  
**Goal:** Acknowledge, classify, resolve or escalate.

1. Confirm sender identity context (account email if provided).  
2. Classify: billing · generation failure · auth · bug · abuse · feature request.  
3. Point to self-serve first when applicable: `/help`, `/help/faq`, `/help/troubleshooting`, `/how-to-use`, `/help/billing`.  
4. For billing/refunds under MoR: explain Paddle processes the payment; collect Paddle transaction identifiers when available.  
5. For technical issues: request browser, OS, approximate time (UTC+5), job/error text, screenshot (no secrets).  
6. Log severity per [SUPPORT_OPERATIONS.md](./SUPPORT_OPERATIONS.md).  
7. Close with clear outcome or next checkpoint.

---

## SOP-02 — AI generation monitoring

**Trigger:** Daily check, user report of failed/stuck generation, Fal balance warning.  
**Systems:** Studio UI · FastAPI worker · Fal.ai (primary) · optional Replicate fallback · credit ledger.

1. Confirm web app healthy (`/api/health`, `/api/ready`).  
2. Confirm worker health (`{FASTAPI_URL}/api/health`).  
3. Check Fal dashboard: balance, recent errors, rate limits (no keys in notes).  
4. Reproduce with a minimal authorized prompt if safe.  
5. Distinguish: user credit exhaustion · provider outage · app bug · content policy refusal.  
6. If provider outage: status note to affected users; consider temporary messaging on Help/Troubleshooting.  
7. If app bug: open defect under SOP-06; do not burn credits diagnosing blindly.  
8. Record credit/COGS anomaly for later finance review (planning, not public metrics).

**Policy reminder:** Identity Preservation is authorized-content only. Do not assist with face-swap, celebrity impersonation, or deepfake abuse. See live `/trust-safety` and `/ai-policy` (legal v1.1).

---

## SOP-03 — Infrastructure health

**Trigger:** Daily cadence or alert.  
**Vendors:** Vercel, Cloudflare, Supabase, GitHub, domain DNS path (Cloudflare/Vercel; Hostinger in domain history).

1. Vercel: production deployment green; runtime error rate stable.  
2. Cloudflare: DNS records match documented zone intent (`docs/RTASSTUDIO-COM-DNS.md`).  
3. Supabase: project available; connection from app OK.  
4. GitHub: CI status on `main`/`master` as configured; no unexpected collaborator adds.  
5. SSL: certificate valid on rtasstudio.com.  
6. On failure: escalate severity; follow [BUSINESS_CONTINUITY_PLAN.md](./BUSINESS_CONTINUITY_PLAN.md).

---

## SOP-04 — Deployment

**Trigger:** Approved change ready for production.  
**Pre-checks:** [docs/RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md) · [CHANGE_MANAGEMENT.md](./CHANGE_MANAGEMENT.md).

1. Confirm branch/commit intended for release.  
2. CI green; lint/typecheck/tests/build as required for the change class.  
3. Confirm Vercel env matches intended production config (no secret dumps in chat).  
4. Deploy via Git push to production branch **or** Vercel promote of known-good build.  
5. Post-deploy smoke: health, ready, login, Studio shell, payments config endpoint.  
6. Watch logs 30–60 minutes for SEV-class regressions.  
7. Record version/commit in release notes or ops log.

**Rollback:** Vercel promote previous production deployment; see [docs/RECOVERY.md](../RECOVERY.md).

---

## SOP-05 — Bug triage

**Trigger:** User report, internal find, CI failure.

1. Reproduce or capture evidence.  
2. Severity: SEV1–SEV4 ([OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md)).  
3. Workaround? Document for support reply.  
4. Fix path: hotfix (emergency change) vs next scheduled release.  
5. Regression test the failing path.  
6. Deploy per SOP-04; notify reporter when fixed.

---

## SOP-06 — Security incident

**Trigger:** Suspected breach, leaked secret, account takeover, abuse of admin surfaces, malware in dependency.

1. Classify as SEV1 until proven otherwise.  
2. Contain: revoke sessions (rotate `NEXTAUTH_SECRET` if needed), rotate exposed keys in Vercel/vaults, disable compromised accounts, fail closed on broken auth/webhooks.  
3. Preserve logs (Vercel, Supabase, GitHub audit) without copying secrets into tickets.  
4. Assess blast radius: users, payments (Paddle — no PAN storage expected), generation jobs, email.  
5. Notify affected users if legally/contractually required and practically identifiable.  
6. Post-incident: update [RISK_REGISTER.md](./RISK_REGISTER.md) and [SECURITY_GOVERNANCE.md](./SECURITY_GOVERNANCE.md) controls.  

**Honesty:** Do not claim SOC 2 / ISO / certified forensics capability. State facts of response only.

Detail baseline: [docs/SECURITY.md](../SECURITY.md) · [docs/FINAL-PRE-LAUNCH-SECURITY-AUDIT.md](../FINAL-PRE-LAUNCH-SECURITY-AUDIT.md).

---

## SOP-07 — Payment / MoR incident

**Trigger:** Checkout failure, webhook storm/silence, double credit grant, refund dispute, MoR approval blockage.

1. Confirm whether **Paddle live checkout** is currently approved/active for rtasstudio.com — do not assume; verify in Paddle dashboard.  
2. Check `/api/payments/config` and webhook processing logs.  
3. Never ask customers for full card numbers; MoR owns card data.  
4. For refunds/chargebacks: follow Paddle MoR process; align with live `/refund` policy (legal v1.1).  
5. If credits out of sync: investigate ledger vs webhook events before manual adjustment; document every manual credit change.  
6. If domain/AUP rejection recurs: freeze marketing claims; use Trust & Safety / AI Policy language only.  
7. Escalate SEV1 if widespread inability to pay when checkout is supposed to be live.

---

## SOP-08 — Customer complaint & escalation

**Trigger:** Repeated dissatisfaction, public complaint, AUP report, chargeback threat.

1. Acknowledge within support RTA.  
2. Separate **product defect**, **expectation mismatch**, **policy enforcement**, and **billing MoR** tracks.  
3. Offer remedy consistent with Terms / Refund policy — do not invent ad-hoc refunds that conflict with MoR.  
4. For abuse/AUP: preserve evidence; refuse prohibited use assistance.  
5. Escalate to Ops Owner for goodwill credits only when policy allows and ledger impact is logged.  
6. Close with written summary to customer.

---

## SOP-09 — Email deliverability

**Trigger:** Bounce spike, users not receiving verification/reset/ready emails.

1. Check Resend domain verification (SPF/DKIM/DMARC as configured).  
2. Confirm Forward Email / routing still delivers inbound aliases to operator mailbox.  
3. Check `EMAIL_FROM` and auth email-config endpoint.  
4. Pause marketing blasts if any; prioritize transactional mail.  
5. Document DNS changes against `docs/RTASSTUDIO-COM-DNS.md` and email ops notes.

---

## SOP-10 — Abuse / Trust & Safety report

**Trigger:** Report of unauthorized likeness, deepfake, harassment, illegal content, or AUP violation.

1. Log time, reporter, URL/job identifiers if available.  
2. Do not regenerate or enhance the abusive content.  
3. Apply account restriction when tooling allows.  
4. Align response with `/trust-safety` and `/ai-policy` (v1.1).  
5. If law-enforcement request: escalate to Ops Owner; do not improvise legal advice.  
6. Notify Paddle if MoR AUP is implicated in payment context.

---

## SOP index

| ID | Name |
|----|------|
| SOP-01 | Customer support intake |
| SOP-02 | AI generation monitoring |
| SOP-03 | Infrastructure health |
| SOP-04 | Deployment |
| SOP-05 | Bug triage |
| SOP-06 | Security incident |
| SOP-07 | Payment / MoR incident |
| SOP-08 | Customer complaint & escalation |
| SOP-09 | Email deliverability |
| SOP-10 | Abuse / Trust & Safety report |

**Owner:** Ops Owner · **Review:** Quarterly  
