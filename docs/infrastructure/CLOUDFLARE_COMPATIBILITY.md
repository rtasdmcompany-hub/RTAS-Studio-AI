# Cloudflare Compatibility — rtasstudio.com + Vercel

**Date:** 2026-07-24  
**Zone:** `rtasstudio.com` (`6d3ba0b62aaf8578052f9da76fdf21ab`)  
**NS:** `dakota.ns.cloudflare.com`, `sierra.ns.cloudflare.com`

---

## DNS Only vs Proxied

| Hostname | Current | Required for Vercel |
|----------|---------|---------------------|
| `rtasstudio.com` (A) | DNS only (`proxied=false`) | **DNS only** |
| `www.rtasstudio.com` (CNAME) | DNS only | **DNS only** |
| MX / TXT / DKIM | Always DNS-only (not proxyable meaningfully) | DNS only |

**Do not enable orange cloud** on apex or www. Vercel KB and community reports: reverse proxy in front of Vercel causes Invalid Configuration, reduced firewall visibility, and SSL 526 failures when modes mismatch.

Source: [Migrate to Vercel from Cloudflare](https://vercel.com/kb/guide/migrate-to-vercel-from-cloudflare)

---

## SSL / TLS

| Item | Status |
|------|--------|
| Edge TLS for site | Terminated by **Vercel** (DNS only path) |
| Cloudflare SSL mode (API) | **Unknown** — token unauthorized for Zone Settings Read (`9109` / `10000`) |
| Founder check | In Cloudflare → SSL/TLS: if all web records are DNS-only, CF SSL mode is largely irrelevant for apex/www traffic |

Recommendation: leave web records gray-clouded; do not put Cloudflare Full/Strict in the critical path for this domain’s primary hosts.

---

## CNAME flattening

| Scenario | Compatible? |
|----------|-------------|
| Flatten apex CNAME → Vercel | Technically possible on CF; **unsafe here** because apex has MX + TXT (RFC1034 / Vercel apex guidance) |
| www CNAME → `….vercel-dns-017.com` | **Yes** — standard subdomain CNAME; keep DNS only |
| www CNAME → `cname.vercel-dns.com` | **Yes** — current; valid |

---

## Root / apex

- Use **A** record(s) to Vercel IPs.
- Keep MX/TXT for mail on the same apex name.
- Do not replace apex A with CNAME.

---

## Redirects (www ↔ apex)

| Layer | Guidance |
|-------|----------|
| Vercel Domains | Preferred — project already redirects www traffic (observed 308 on `www…/api/ready`) |
| Cloudflare Page Rules / Redirect Rules | Avoid duplicating conflicting redirects while DNS-only |
| Canonical host | Apex is primary production URL per env (`https://rtasstudio.com`) |

---

## Email Routing vs Forward Email

Historical scripts reference Cloudflare Email Routing API (often 403 without extra token scopes). Production inbound currently uses **Forward Email DNS** (MX + TXT), not CF Email Routing API. Do not enable CF Email Routing MX that would conflict with Forward Email without a planned cutover.

---

## Token capability note

Present token can **list DNS records** (read). Cannot read SSL/always_https settings. For documentation completeness, founder can screenshot SSL/TLS overview; no change required for DNS-only setup.
