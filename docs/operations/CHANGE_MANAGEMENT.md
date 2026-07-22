# Change Management — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Effective:** 22 July 2026  
**Related:** [docs/RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md) · [docs/RELEASE_NOTES.md](../RELEASE_NOTES.md) · [docs/VERSION-HISTORY.md](../VERSION-HISTORY.md) · [docs/RECOVERY.md](../RECOVERY.md) · [docs/GITHUB-BRANCH-PROTECTION.md](../GITHUB-BRANCH-PROTECTION.md) · [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md)

---

## 1. Purpose

Control how production changes are proposed, approved, released, monitored, and rolled back — including emergency fixes — without inventing a bureaucracy the founder-operated team cannot run.

---

## 2. Change classes

| Class | Examples | Approval | Lead time |
|-------|----------|----------|-----------|
| **Standard** | Features, refactors, docs-only, non-urgent fixes | Ops Owner (self-approve with checklist) | Normal PR cycle |
| **Normal significant** | Auth, payments/webhooks, credits math, schema, DNS, OAuth console | Explicit Ops Owner go/no-go + backup awareness | Prefer off-peak |
| **Emergency** | SEV1/SEV2 production break, active security exposure | Ops Owner immediate; document after | ASAP |
| **Vendor / config** | Vercel env, Paddle products, Cloudflare DNS, Fal plan | Ops Owner; dual-check DNS/payment | Same as significant |

Documentation-only changes under `docs/` and `business/` follow Standard class and do not require app smoke tests, but still require accurate fact hygiene (pricing, MoR, legal version).

---

## 3. Versioning

| Artifact | Practice |
|----------|----------|
| Application | Git commits on mainline; Vercel deployment IDs as release fingerprints |
| Legal suite | Versioned policy set (currently **v1.1** live) — bump with deliberate sign-off |
| Ops docs | Effective date + quarterly review stamp |
| Shared packages | Workspace versioning as used by monorepo releases |

Record user-visible changes in release notes / changelog (`/help/changelog` when shipped).

---

## 4. Release process (standard)

1. **Develop** on branch; keep secrets out of git.  
2. **Validate** — CI, lint, typecheck, tests, build as applicable (`docs/RELEASE-CHECKLIST.md`).  
3. **Review** — PR description: why, risk, rollback plan.  
4. **Approve** — Ops Owner merge authority.  
5. **Deploy** — production branch → Vercel (or promote).  
6. **Verify** — `/api/health`, `/api/ready`, login, Studio, payments config if touched.  
7. **Monitor** — 30–60 minutes logs.  
8. **Close** — note commit/deployment in ops log.

---

## 5. Approval matrix (current stage)

| Change type | Required approver |
|-------------|-------------------|
| Marketing copy / help docs | Ops Owner |
| Legal policy text | Ops Owner (+ external counsel when engaged) |
| Pricing constants | Ops Owner — must match live packaging ($5 / $89 / $249) |
| Payment / MoR configuration | Ops Owner |
| Production DNS | Ops Owner |
| Emergency hotfix | Ops Owner (post-facto write-up within 48 hours) |

There is no separate CAB. If headcount grows, introduce a second reviewer for Significant and Emergency classes.

---

## 6. Rollback

| Situation | Action |
|-----------|--------|
| Bad application deploy | Vercel → prior production deployment → Promote |
| Bad env var | Fix env → Redeploy (promote alone may keep bad env) |
| Bad git commit | `git revert` + push after traffic stabilized |
| Bad DNS | Restore from `docs/RTASSTUDIO-COM-DNS.md` |
| Bad schema migration | Follow DB restore playbook in continuity plan — prefer validate-then-cutover |

Rollback success criteria: health + ready + auth + critical path for the change class.

---

## 7. Emergency change procedure

1. Declare SEV and freeze unrelated releases.  
2. Implement minimal fix or rollback.  
3. Deploy with abbreviated tests focused on the failure mode.  
4. Verify and communicate.  
5. Within 48 hours: write incident note — trigger, fix, prevention, whether Risk Register updates.  
6. Schedule follow-up hardening if emergency skipped controls.

Emergency does **not** authorize committing secrets or disabling webhook verification permanently.

---

## 8. Forbidden without explicit exception

- Force-push to main/master  
- Skipping production fail-closed payment/auth checks to “just make checkout work”  
- Editing live legal version numbers without content review  
- Claiming certifications in release marketing  

---

## 9. MoR / commercial change gate

Any change that alters payment UX, AUP marketing claims, or Identity Preservation framing must be checked against Paddle AUP readiness and legal v1.1. If checkout/domain approval is still pending, do not announce “payments fully live” in release notes.

---

## 10. Metrics (manual)

Track quarterly: count of production deploys, emergency changes, rollbacks, SEV1 from change failure. Goals are internal quality signals, not customer SLAs.

**Owner:** Ops Owner · **Review:** Quarterly · **Phase 11 Sprint 6**
