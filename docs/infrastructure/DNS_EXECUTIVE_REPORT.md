# DNS Migration — Executive Report (CTO)

**Product:** RTAS Studio AI  
**Domain:** `rtasstudio.com`  
**Date:** 2026-07-24  
**Scope:** Read-only audit + documentation. **No production DNS mutations performed.**

---

## Scorecard

| Question | Answer |
|----------|--------|
| **Current DNS Status** | Healthy on Cloudflare. Apex `A 76.76.21.21`, www `CNAME cname.vercel-dns.com`, both DNS-only. Forward Email MX + Resend DKIM/SPF live. |
| **Migration Required?** | **No** (for uptime / validity). Vercel `misconfigured: false`, `ipStatus: optional-change`. |
| **Risk Level** | **Low** if only DMARC added; **Low–Medium** if www CNAME updated; **Medium** if apex switches to rank-1 dual A (regional reachability reports). |
| **Downtime Risk** | Near-zero for DMARC add. Brief DNS cache lag (≤ minutes) for www CNAME edit. Apex IP swap is the only meaningful outage vector. |
| **Rollback Ready?** | **Yes** — exact known-good values in `DNS_ROLLBACK_PLAN.md`. |
| **Email Safe?** | **Yes** if mail records untouched. Resend **verified**. DMARC add is safe at `p=none`. |
| **Production Ready?** | **Yes** — apex `/api/ready` 200; DNS valid. |
| **Verdict** | **PASS WITH MINOR ACTIONS** |

---

## Current vs recommended (evidence)

| Host | Current (live) | Official docs | Vercel API rank-1 | Decision |
|------|----------------|---------------|-------------------|----------|
| `@` | A `76.76.21.21` | Apex **A** (not CNAME) | A `216.198.79.1` + `64.29.17.1` | **Keep current** |
| `www` | CNAME `cname.vercel-dns.com` | Project CNAME / `vercel-dns-017` style | `598c94a249a55317.vercel-dns-017.com` | **Optional** upgrade |
| Mail | Forward Email + Resend | Unrelated to web host | — | **Do not change** |
| DMARC | Missing | Best practice | — | **Add `p=none`** |

**Hypothesis rejected:** “CNAME @ → vercel-dns-017” — **not** official for this apex (MX/TXT present; Vercel + RFC1034).

---

## Minor actions (founder)

1. **ADD** TXT `_dmarc` → `v=DMARC1; p=none; rua=mailto:admin@rtasstudio.com; fo=1`
2. **Optional EDIT** www CNAME → `598c94a249a55317.vercel-dns-017.com` (DNS only)
3. **Do not** change apex to CNAME; **do not** orange-cloud; **do not** touch MX/SPF/DKIM

Full sheet: `MANUAL_CLOUDFLARE_CHANGE_LIST.md`

---

## Document index

| File | Role |
|------|------|
| `DNS_AUDIT_BEFORE.md` | Full inventory |
| `DNS_DIFF_REPORT.md` | Legacy vs new |
| `DNS_PRODUCTION_DEPLOYMENT.md` | Deployment / migration guide |
| `DNS_COMPATIBILITY_REPORT.md` | Email/Paddle safety |
| `CLOUDFLARE_COMPATIBILITY.md` | Proxy/SSL/flattening |
| `DNS_ROLLBACK_PLAN.md` | Rollback |
| `PRODUCTION_DNS_CHECKLIST.md` | Verification |
| `EMAIL_SECURITY_AUDIT.md` | SPF/DKIM/DMARC |
| `MANUAL_CLOUDFLARE_CHANGE_LIST.md` | Founder apply list |
| `DNS_EXECUTIVE_REPORT.md` | This report |

---

## Sources

- Live DNS: Google Public DNS DoH (2026-07-24)
- Cloudflare DNS Records API GET (read-only)
- Vercel `GET /v6/domains/rtasstudio.com/config`
- Resend domains GET
- https://vercel.com/docs/domains/set-up-custom-domain
- https://vercel.com/docs/domains/working-with-domains/add-a-domain
- https://vercel.com/docs/domains/troubleshooting
- https://vercel.com/kb/guide/migrate-to-vercel-from-cloudflare
