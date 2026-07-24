# MANUAL CLOUDFLARE CHANGE LIST — Founder Apply Only

**Domain:** `rtasstudio.com`  
**Zone:** Cloudflare (active)  
**Agent rule:** These changes were **NOT** applied by automation. Founder applies manually in Cloudflare → DNS → Records.

---

## Priority 0 — Do nothing to mail (permanent for this migration)

| Action | Type | Name | Content |
|--------|------|------|---------|
| **DO NOT TOUCH** | MX | `@` / `rtasstudio.com` | `mx1.forwardemail.net` / `mx2.forwardemail.net` |
| **DO NOT TOUCH** | TXT | `@` | SPF `v=spf1 include:spf.forwardemail.net include:amazonses.com ~all` |
| **DO NOT TOUCH** | TXT | `@` | `forward-email=…` alias map |
| **DO NOT TOUCH** | TXT | `resend._domainkey` | Resend DKIM |
| **DO NOT TOUCH** | MX/TXT | `send` | Resend SES SPF pair |

---

## Priority 1 — Recommended (security, additive)

### ADD

| Field | Value |
|-------|-------|
| Type | **TXT** |
| Name | `_dmarc` |
| Content | `v=DMARC1; p=none; rua=mailto:admin@rtasstudio.com; fo=1` |
| TTL | Auto |
| Proxy | Off / N/A |

**Why:** DMARC missing; monitor-only policy; no impact on Vercel web DNS.

---

## Priority 2 — Optional (Vercel project-specific www)

### EDIT (only if choosing optional alignment)

| Field | From (current) | To (Vercel rank-1 API) |
|-------|----------------|-------------------------|
| Type | CNAME | CNAME |
| Name | `www` | `www` |
| Content | `cname.vercel-dns.com` | `598c94a249a55317.vercel-dns-017.com` |
| Proxy | **DNS only** | **DNS only** (must stay Off) |

**Why optional:** Current target is valid (`misconfigured: false`). New hostname is project-specific per Vercel API.

**Rollback:** set content back to `cname.vercel-dns.com`, Proxy Off.

---

## Priority 3 — Optional / higher caution (apex A)

### NOT recommended while production is healthy

Vercel API rank-1 suggests replacing:

| Current | Rank-1 suggestion |
|---------|-------------------|
| Single A `@` → `76.76.21.21` | Two A records: `216.198.79.1` and `64.29.17.1` |

Vercel also reports `ipStatus: optional-change` and community reports of regional reachability issues on those `.1` endpoints.

| Decision | Guidance |
|----------|----------|
| Default | **Keep** `A @ 76.76.21.21`, Proxy **Off** |
| If leadership insists | Schedule window; add dual A; remove old A only after both new A work; keep Proxy Off; follow `DNS_ROLLBACK_PLAN.md` |

---

## Forbidden changes

| Change | Reason |
|--------|--------|
| ADD CNAME `@` → any `*.vercel-dns-017.com` | Breaks RFC1034 with MX/TXT; not official apex guidance for this zone |
| Enable Proxy (orange cloud) on `@` or `www` | Vercel SSL / Invalid Configuration risk |
| Delete / replace entire zone via scripts | Can wipe mail records |
| Hostinger DNS writes | NS authority is Cloudflare; Hostinger zone is not live |

---

## After any apply

1. Run `docs/infrastructure/PRODUCTION_DNS_CHECKLIST.md`
2. Confirm Resend still Verified
3. Confirm `https://rtasstudio.com/api/ready` → 200
