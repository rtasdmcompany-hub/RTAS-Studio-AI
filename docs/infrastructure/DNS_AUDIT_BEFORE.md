# DNS Audit — Before Migration (rtasstudio.com)

**Audit time:** 2026-07-24T08:10:10Z (UTC)  
**Mode:** Read-only (Google Public DNS DoH + Cloudflare DNS API GET + Vercel domains config GET + Resend domains GET)  
**Mutations performed:** None  
**Authority:** Cloudflare (`dakota.ns.cloudflare.com`, `sierra.ns.cloudflare.com`)  
**Zone ID:** `6d3ba0b62aaf8578052f9da76fdf21ab` (status: active)

---

## 1. Nameservers (public)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| NS | `rtasstudio.com` | `dakota.ns.cloudflare.com.` | 21600 |
| NS | `rtasstudio.com` | `sierra.ns.cloudflare.com.` | 21600 |

SOA (public): `dakota.ns.cloudflare.com. dns.cloudflare.com. 2410197583 10000 2400 604800 1800`

---

## 2. Apex / root (`rtasstudio.com`)

| Type | Value | TTL | Cloudflare proxied | Notes |
|------|-------|-----|--------------------|-------|
| A | `76.76.21.21` | 300 | **DNS only** (`proxied=false`) | Vercel legacy anycast; matches Vercel `recommendedIPv4` **rank 2** |
| AAAA | *(none)* | — | — | No AAAA published |
| CNAME | *(none)* | — | — | Correct: apex has MX/TXT — CNAME @ forbidden by RFC1034 |

### Apex MX (inbound mail — Forward Email)

| Type | Priority | Value | Proxied |
|------|----------|-------|---------|
| MX | 10 | `mx1.forwardemail.net` | DNS only |
| MX | 10 | `mx2.forwardemail.net` | DNS only |

### Apex TXT

| Purpose | Value (as published) |
|---------|----------------------|
| SPF | `v=spf1 include:spf.forwardemail.net include:amazonses.com ~all` |
| Forward Email aliases | `forward-email=info:<gmail>,support:<gmail>,contact:<gmail>,admin:<gmail>,auth:<gmail>` (destination redacted in this doc; live in public DNS) |

---

## 3. `www.rtasstudio.com`

| Type | Value | TTL | Proxied |
|------|-------|-----|---------|
| CNAME | `cname.vercel-dns.com.` | 300 | **DNS only** |

Resolved A (via CNAME chain at audit time): Vercel edge IPs behind `cname.vercel-dns.com` (observed e.g. `66.33.60.35`, `76.76.21.123` — dynamic).

---

## 4. Resend / outbound email auth

| Host | Type | Value | Resend API status |
|------|------|-------|-------------------|
| `resend._domainkey.rtasstudio.com` | TXT | `p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDIOnuBZulEF5WVPIf1+IbYcJsKpWgmve0iMPwcg9…` (full key in live DNS) | **verified** |
| `send.rtasstudio.com` | MX 10 | `feedback-smtp.us-east-1.amazonses.com` | **verified** |
| `send.rtasstudio.com` | TXT | `v=spf1 include:amazonses.com ~all` | **verified** |

Resend domain object: `rtasstudio.com` — **status: verified**, sending enabled, region `us-east-1`.

---

## 5. DMARC

| Host | Type | Result |
|------|------|--------|
| `_dmarc.rtasstudio.com` | TXT | **Missing** (NXDOMAIN / no Answer; Status 3 from Google DoH) |

---

## 6. Paddle / payment verification TXT

No Paddle-specific TXT/CNAME observed at apex or common verification hosts in this zone snapshot (9 Cloudflare records total). Paddle webhook/checkout URLs are application/env config, not DNS in current zone.

---

## 7. Cloudflare zone record inventory (API GET)

All 9 records were **DNS only** (gray cloud / not proxied):

1. `A` `rtasstudio.com` → `76.76.21.21`
2. `CNAME` `www.rtasstudio.com` → `cname.vercel-dns.com`
3. `MX` `rtasstudio.com` → `mx1.forwardemail.net` (prio 10)
4. `MX` `rtasstudio.com` → `mx2.forwardemail.net` (prio 10)
5. `MX` `send.rtasstudio.com` → `feedback-smtp.us-east-1.amazonses.com` (prio 10)
6. `TXT` `resend._domainkey.rtasstudio.com` → Resend DKIM
7. `TXT` `rtasstudio.com` → `forward-email=…`
8. `TXT` `rtasstudio.com` → apex SPF
9. `TXT` `send.rtasstudio.com` → Resend/Amazon SES SPF

### Cloudflare settings API limitation

| Setting | Result |
|---------|--------|
| `GET …/settings/ssl` | **Unauthorized** (code 9109) — token lacks Zone Settings Read |
| `GET …/settings/always_use_https` | **Authentication error** (code 10000) |

Proxy mode for DNS records **was** readable via DNS Records API (`proxied: false` on all listed records).

---

## 8. Vercel domain config (API evidence)

Source: `GET https://api.vercel.com/v6/domains/rtasstudio.com/config`

| Field | Value |
|-------|-------|
| `misconfigured` | **false** |
| `configuredBy` | `A` |
| `serviceType` | `external` |
| `aValues` | `["76.76.21.21"]` |
| `cnames` | `[]` |
| `ipStatus` | `optional-change` |
| `conflicts` | `[]` |
| Nameservers seen by Vercel | Cloudflare (`dakota` / `sierra`) |

### Recommended targets (project-specific)

| Rank | Type | Values |
|------|------|--------|
| 1 | A (apex) | `216.198.79.1`, `64.29.17.1` |
| 2 | A (apex) | `76.76.21.21` ← **current** |
| 1 | CNAME (subdomain/`www`) | `598c94a249a55317.vercel-dns-017.com.` |
| 2 | CNAME | `cname.vercel-dns.com.` ← **current www** |

---

## 9. Live HTTP (post-DNS)

| URL | Result |
|-----|--------|
| `https://rtasstudio.com/api/ready` | **200** `{"status":"ready","service":"rtas-web",…}` |
| `https://www.rtasstudio.com/api/ready` | **308** redirect (www → apex path; expected if Vercel redirect configured) |

---

## 10. Evidence sources

- Google DoH: `https://dns.google/resolve?name=…&type=…`
- Cloudflare API GET zone + DNS records (no writes)
- Vercel domain config API
- Resend domains API (GET only; no verify POST)
- Official Vercel docs (see `DNS_DIFF_REPORT.md` citations)

**Raw working dump (local, may contain public mailbox strings):** `docs/_dns_live_audit.json` — do not treat as a required commit artifact; redact before sharing externally.
