# DNS Rollback Plan — rtasstudio.com

**Purpose:** Restore known-good web DNS within minutes if an optional Vercel target change causes issues.  
**Mail records:** Never part of forward migration; rollback of web records must still leave mail intact.

---

## Known-good snapshot (2026-07-24 — production verified)

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `rtasstudio.com` | `76.76.21.21` | Off |
| CNAME | `www.rtasstudio.com` | `cname.vercel-dns.com` | Off |
| MX | `rtasstudio.com` | `mx1.forwardemail.net` prio 10 | — |
| MX | `rtasstudio.com` | `mx2.forwardemail.net` prio 10 | — |
| TXT | `rtasstudio.com` | apex SPF (`v=spf1 include:spf.forwardemail.net include:amazonses.com ~all`) | — |
| TXT | `rtasstudio.com` | `forward-email=…` (alias map) | — |
| TXT | `resend._domainkey.rtasstudio.com` | Resend DKIM `p=…` | — |
| MX | `send.rtasstudio.com` | `feedback-smtp.us-east-1.amazonses.com` prio 10 | — |
| TXT | `send.rtasstudio.com` | `v=spf1 include:amazonses.com ~all` | — |

**Evidence of good:** Vercel `misconfigured: false`; `https://rtasstudio.com/api/ready` → 200; Resend **verified**.

---

## Rollback triggers

- Vercel Domains shows Invalid / Misconfigured after a change
- Homepage / studio / login fail while `*.vercel.app` still works
- SSL errors (526, certificate name mismatch)
- Regional timeouts after switching to rank-1 apex IPs
- Accidental mail breakage (inbound bounce / Resend unverified) — restore mail rows from snapshot immediately

---

## Rollback procedure (Cloudflare UI — manual)

1. Open Cloudflare → DNS → Records for `rtasstudio.com`.
2. If www was changed: set CNAME `www` → `cname.vercel-dns.com`, **Proxy off**.
3. If apex A was changed: delete new A records (`216.198.79.1`, `64.29.17.1`, etc.) and ensure single A `@` → `76.76.21.21`, **Proxy off**.
4. If an apex CNAME was mistakenly added: **delete it**; restore A + ensure MX/TXT still present.
5. Do **not** delete MX/TXT/DKIM while rolling back web targets.
6. Wait up to 5–30 minutes (TTL 300 observed); purge local DNS cache if needed.
7. Verify checklist in `PRODUCTION_DNS_CHECKLIST.md`.

---

## Rollback of DMARC only

If `_dmarc` was added and causes unexpected mail disposition issues (unlikely at `p=none`):

- Delete TXT `_dmarc.rtasstudio.com`, or set `p=none` with no quarantine/reject.

---

## NS / provider rollback

Nameservers are already on Cloudflare and healthy. **Do not** flip NS back to Hostinger/Vercel unless Cloudflare zone is lost — that is a separate disaster recovery, not part of this optional target tweak.

---

## Rollback readiness

| Item | Status |
|------|--------|
| Exact prior values documented | **Yes** (this file + `DNS_AUDIT_BEFORE.md`) |
| Mail values documented | **Yes** |
| Can restore without API scripts | **Yes** (manual CF UI) |
| Automated rollback scripts | Available historically under `apps/web/scripts/` but **must not be run** without review (some overwrite entire zones) |
