# rtasstudio.com — activation status

**Updated:** 24 July 2026 (DNS infrastructure audit — documentation only; no DNS mutations)

## Authoritative DNS docs

See **`docs/infrastructure/`** for the production DNS package:

- Executive verdict: [`docs/infrastructure/DNS_EXECUTIVE_REPORT.md`](./infrastructure/DNS_EXECUTIVE_REPORT.md)
- Founder manual change list: [`docs/infrastructure/MANUAL_CLOUDFLARE_CHANGE_LIST.md`](./infrastructure/MANUAL_CLOUDFLARE_CHANGE_LIST.md)
- Full pre-change inventory: [`docs/infrastructure/DNS_AUDIT_BEFORE.md`](./infrastructure/DNS_AUDIT_BEFORE.md)

## Live now (verified 24 Jul 2026)

| Check | Result |
|------|--------|
| Nameservers | Cloudflare (`dakota` / `sierra`) |
| Apex A | `76.76.21.21` (DNS only) — Vercel valid (`misconfigured: false`) |
| www | CNAME `cname.vercel-dns.com` (DNS only) |
| `https://rtasstudio.com/api/ready` | **200 ready** |
| Inbound MX | Forward Email (`mx1` / `mx2.forwardemail.net`) |
| Resend domain | **Verified** (DKIM + `send.` SPF) |
| DMARC | **Missing** — recommended add (`p=none`); see email audit |
| Vercel target migration | **Not required** (`ipStatus: optional-change`) |

## Still recommended (manual, non-blocking)

1. Add DMARC TXT at `_dmarc` (monitor mode) — see infrastructure manual change list.
2. Optional: align www CNAME to project-specific `598c94a249a55317.vercel-dns-017.com` (DNS only).
3. **Do not** set apex CNAME (breaks MX). **Do not** orange-cloud apex/www.

## What works for users right now

1. Open **https://rtasstudio.com**
2. Sign up / Google sign-in
3. Transactional email via Resend (`noreply` / auth aliases per env)
4. Inbound aliases (`info` / `support` / `contact` / `admin` / `auth`) via Forward Email

## Historical note (21 July 2026)

Earlier notes referenced Hostinger DNS and pending Resend verification. As of this audit, DNS authority is **Cloudflare**, Resend is **verified**, and Hostinger is not the live zone.
