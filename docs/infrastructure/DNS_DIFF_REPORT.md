# DNS Diff Report — Legacy vs Current Official / Project Targets

**Domain:** `rtasstudio.com`  
**Audit:** 2026-07-24 (see `DNS_AUDIT_BEFORE.md`)  
**Rule:** Evidence-only. No production DNS was changed while producing this report.

---

## Official Vercel documentation (verified 2026-07-24)

| Claim | Source | Status |
|-------|--------|--------|
| Apex domains use an **A** record (not CNAME) | [Set up a custom domain](https://vercel.com/docs/domains/set-up-custom-domain) (updated 2026-06-15); [Add a domain](https://vercel.com/docs/domains/working-with-domains/add-a-domain) | Confirmed |
| General-purpose apex A example: `76.76.21.21` | Same CLI docs note | Confirmed as **general-purpose / fallback** |
| Subdomains use **CNAME**; project may get unique host like `….vercel-dns-017.com` | [Add a domain](https://vercel.com/docs/domains/working-with-domains/add-a-domain) example `d1d4fc829fe7bc7c.vercel-dns-017.com` | Confirmed |
| DNS RFC forbids CNAME at apex when other RRs (NS, MX, TXT) exist | [Troubleshooting — Working with Apex domain](https://vercel.com/docs/domains/troubleshooting); [Deploying & Redirecting](https://vercel.com/docs/domains/working-with-domains/deploying-and-redirecting) citing RFC1034 §3.6.2 | Confirmed |
| Prefer `www` + CNAME for CDN steering; apex A still supported via Anycast | [Deploying & Redirecting](https://vercel.com/docs/domains/working-with-domains/deploying-and-redirecting) | Confirmed |
| Cloudflare: gray-cloud (DNS only) when pointing to Vercel | [Migrate to Vercel from Cloudflare](https://vercel.com/kb/guide/migrate-to-vercel-from-cloudflare) | Confirmed |

### Explicit rejection of “CNAME @ → vercel-dns-017”

The CTO draft hypothesis (“Latest: CNAME @ → vercel-dns-017”) is **not** the official apex recommendation for zones that also host **MX + SPF/TXT**.

For `rtasstudio.com`, apex currently has Forward Email **MX** and multiple **TXT** records. Publishing a CNAME at `@` would violate RFC1034 and risk breaking inbound mail. **Do not apply CNAME flattening at apex for this migration.**

Cloudflare *can* flatten apex CNAMEs, but Vercel’s own troubleshooting docs still instruct apex **A** when MX/other data exists. Treat apex CNAME as **out of scope / unsafe** for this production zone.

---

## Current live vs Vercel API recommendations

| Record | Live now | Vercel rank 2 (legacy / general) | Vercel rank 1 (project) | Action |
|--------|----------|----------------------------------|-------------------------|--------|
| Apex A | `76.76.21.21` | `76.76.21.21` | `216.198.79.1` **and** `64.29.17.1` | **Optional** (`ipStatus: optional-change`). Production `misconfigured: false`. |
| www CNAME | `cname.vercel-dns.com` | `cname.vercel-dns.com.` | `598c94a249a55317.vercel-dns-017.com.` | **Optional** alignment to project-specific target |
| Apex CNAME | none | n/a (not recommended with MX) | n/a | **Do not add** |
| Mail MX / TXT / DKIM | Forward Email + Resend | n/a | n/a | **Do not change** |
| `_dmarc` | missing | n/a | n/a | **Recommended add** (security; see `EMAIL_SECURITY_AUDIT.md`) |

---

## Deprecated / legacy labels

| Label | Meaning for RTAS |
|-------|------------------|
| **Legacy Vercel A** | Single A `@` → `76.76.21.21` — still accepted (rank 2); currently live and valid |
| **Legacy www CNAME** | `cname.vercel-dns.com` — still accepted (rank 2); currently live and valid |
| **Project-specific www CNAME** | `598c94a249a55317.vercel-dns-017.com.` — Vercel API rank 1 for this domain |
| **Project-specific apex A pair** | `216.198.79.1` + `64.29.17.1` — Vercel API rank 1; **optional** |

### Caution on rank-1 apex IPs

Community reports (2026) describe intermittent reachability to `216.198.79.1` / `64.29.17.1` from some regions (notably Brazil), with legacy `76.76.21.x` continuing to work. Sources: Vercel Community threads on those exact IPs. Combined with `ipStatus: optional-change` and `misconfigured: false`, **forced apex IP migration is not justified for uptime**.

---

## Required changes vs optional changes

### Required for production correctness

**None.** Site resolves, Vercel reports valid config, Resend verified, Forward Email MX live.

### Recommended (non-blocking)

1. Add DMARC TXT at `_dmarc` (`p=none` monitor mode).
2. Optionally update **www only** CNAME → `598c94a249a55317.vercel-dns-017.com` (DNS only).

### Explicitly not recommended now

1. Apex CNAME / CNAME flattening to any `vercel-dns-017` host.
2. Replacing working apex A `76.76.21.21` with rank-1 dual A unless Vercel marks the domain misconfigured or a planned maintenance window is approved.
3. Any change to MX, SPF, `forward-email=`, `send.*`, or `resend._domainkey`.
4. Enabling Cloudflare orange-cloud proxy on apex/www.

---

## Diff summary (one line)

Current = **valid legacy Vercel targets** on Cloudflare DNS-only; latest **project-specific** targets exist as **optional** upgrades for www (CNAME) and apex (dual A); **mail untouched**; **DMARC missing**.
