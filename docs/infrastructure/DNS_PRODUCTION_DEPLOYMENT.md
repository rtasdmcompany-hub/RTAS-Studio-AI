# Production DNS Deployment Guide — rtasstudio.com (Vercel + Cloudflare)

**Last verified:** 2026-07-24  
**DNS authority:** Cloudflare  
**App host:** Vercel  
**Inbound mail:** Forward Email (`mx1`/`mx2.forwardemail.net`)  
**Outbound mail:** Resend (DKIM + `send.` Amazon SES SPF)  
**Critical rule:** Do not auto-mutate production DNS. Apply changes only via the founder’s Cloudflare dashboard using the manual change list.

---

## Architecture (current, working)

```
Registrar NS → Cloudflare
  ├─ A    @      → 76.76.21.21          (Vercel, DNS only)
  ├─ CNAME www   → cname.vercel-dns.com (Vercel, DNS only)
  ├─ MX   @      → Forward Email        (DNS only)  ← DO NOT CHANGE
  ├─ TXT  @      → SPF + forward-email  ← DO NOT CHANGE
  ├─ TXT  resend._domainkey → Resend DKIM (verified)
  └─ MX/TXT send → Resend SES SPF (verified)
```

Live checks (2026-07-24):

- `https://rtasstudio.com/api/ready` → 200 ready
- Vercel `misconfigured: false`, `configuredBy: "A"`, `ipStatus: "optional-change"`
- Resend domain status: **verified**

---

## Official recommendation (evidence-based)

### Apex (`@` / `rtasstudio.com`)

| Item | Recommendation |
|------|----------------|
| Record type | **A** (not CNAME) |
| Why not CNAME @ | Zone has MX + TXT; RFC1034 forbids CNAME coexisting with other data at the node. Vercel docs agree. |
| Legacy / current | `A @ → 76.76.21.21` |
| Latest project rank-1 (API) | `A @ → 216.198.79.1` **and** `A @ → 64.29.17.1` |
| Decision | **Keep current A** unless Vercel flips to misconfigured or leadership schedules an optional upgrade |

Sources:

- https://vercel.com/docs/domains/set-up-custom-domain
- https://vercel.com/docs/domains/working-with-domains/add-a-domain
- https://vercel.com/docs/domains/troubleshooting
- Project API: `GET /v6/domains/rtasstudio.com/config`

### `www`

| Item | Recommendation |
|------|----------------|
| Record type | **CNAME** |
| Legacy / current | `www → cname.vercel-dns.com` |
| Latest project rank-1 (API) | `www → 598c94a249a55317.vercel-dns-017.com` |
| Proxy | **DNS only** (gray cloud) |
| Decision | Optional upgrade to project-specific hostname; not required for validity |

### Mail (all environments)

**Do not recommend changing mail records** as part of any Vercel DNS “migration.”

Leave untouched:

- Apex MX → Forward Email
- Apex SPF / `forward-email=` TXT
- `resend._domainkey` TXT
- `send` MX + TXT

---

## Cloudflare compatibility notes

| Topic | Guidance |
|-------|----------|
| DNS Only vs Proxied | Apex + www **must stay DNS only** for Vercel SSL/ACME and to avoid “Invalid Configuration” / 526 issues when orange-clouded |
| SSL mode | Prefer Vercel-terminated TLS. Token lacked Zone Settings Read — confirm manually in CF UI if proxy ever enabled elsewhere |
| CNAME flattening | Available on Cloudflare but **do not use apex CNAME** for this zone (MX conflict) |
| Root vs www | Keep both; Vercel redirect handles canonical host (www currently 308s to apex path) |
| Redirects | Prefer Vercel Domains redirect settings over Cloudflare Page Rules for app traffic |

Full detail: `CLOUDFLARE_COMPATIBILITY.md`

---

## Migration playbook (optional www alignment only)

1. Snapshot Cloudflare DNS (export / screenshot) — see checklist.
2. Edit **only** `www` CNAME → `598c94a249a55317.vercel-dns-017.com`, proxied **off**.
3. Wait TTL (~5 minutes; public TTL observed 300s).
4. Verify: `dig www.rtasstudio.com CNAME`, Vercel Domains UI, `https://www.rtasstudio.com`.
5. Confirm mail unchanged: `dig MX rtasstudio.com`, Resend dashboard still Verified.

Apex dual-A upgrade is documented as optional and higher-caution — see `DNS_DIFF_REPORT.md` and `DNS_ROLLBACK_PLAN.md`.

---

## Related docs in this folder

| Doc | Purpose |
|-----|---------|
| `DNS_AUDIT_BEFORE.md` | Full pre-change inventory |
| `DNS_DIFF_REPORT.md` | Legacy vs new targets |
| `DNS_COMPATIBILITY_REPORT.md` | Email / Paddle / TXT safety |
| `CLOUDFLARE_COMPATIBILITY.md` | Proxy / SSL / flattening |
| `DNS_ROLLBACK_PLAN.md` | Instant rollback values |
| `PRODUCTION_DNS_CHECKLIST.md` | Go-live verification |
| `EMAIL_SECURITY_AUDIT.md` | SPF/DKIM/DMARC |
| `DNS_EXECUTIVE_REPORT.md` | Verdict + manual change list |
| `MANUAL_CLOUDFLARE_CHANGE_LIST.md` | Founder action sheet |

Also update legacy note: `docs/RTASSTUDIO-COM-DNS.md` (points here for DNS authority).
