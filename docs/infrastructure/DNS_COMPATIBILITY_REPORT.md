# DNS Compatibility Report — Email, Paddle, Verification TXT

**Date:** 2026-07-24  
**Question:** Can optional Vercel target updates proceed without breaking email, Paddle, or verification records?

---

## Verdict

| Surface | Safe if apex/www web targets change? | Notes |
|---------|--------------------------------------|-------|
| Forward Email inbound MX | **Yes — if MX untouched** | Apex MX must remain `mx1`/`mx2.forwardemail.net` |
| Apex SPF + `forward-email=` TXT | **Yes — if TXT untouched** | Required for inbound routing + SPF |
| Resend DKIM | **Yes — if `resend._domainkey` untouched** | Currently **verified** |
| Resend `send.` SPF (MX+TXT) | **Yes — if `send.*` untouched** | Currently **verified** |
| DMARC | N/A (missing) | Adding `_dmarc` is additive and safe |
| Paddle checkout / webhooks | **Yes** | No Paddle DNS TXT in zone; uses HTTPS app URLs |
| Vercel SSL / ACME | **Yes** if records stay **DNS only** | Proxy off |
| Apex CNAME migration | **No** | Would conflict with MX/TXT |

---

## Email stack (do not modify during web DNS tweaks)

### Inbound (Forward Email)

- MX `@` → `mx1.forwardemail.net`, `mx2.forwardemail.net` (prio 10)
- TXT `@` → `forward-email=info:…,support:…,contact:…,admin:…,auth:…`
- Apex SPF includes `include:spf.forwardemail.net`

### Outbound (Resend)

- TXT `resend._domainkey` → DKIM public key (**verified**)
- MX `send` → `feedback-smtp.us-east-1.amazonses.com` (**verified**)
- TXT `send` → `v=spf1 include:amazonses.com ~all` (**verified**)

Changing apex A or www CNAME does **not** require touching these records.

---

## Paddle

| Check | Result |
|-------|--------|
| Paddle DNS verification record in CF zone | **Not present** in 9-record inventory |
| Impact of www/apex web DNS change | **None expected** — billing uses application endpoints / env (`PADDLE_*`) |
| Post-change verify | Hit pricing checkout + webhook delivery logs (app-level, not DNS) |

---

## Other TXT / verification

| Record | Present? | Keep? |
|--------|----------|-------|
| Apex SPF | Yes | Keep |
| Forward Email map | Yes | Keep |
| Resend DKIM | Yes | Keep |
| DMARC | No | Add separately (see email audit) |
| Google site verification / ACME TXT | Not in current inventory | N/A |

---

## Unsafe combinations

1. **Apex CNAME + MX** — breaks or is rejected; do not.
2. **Orange-cloud proxy on apex/www** — known Vercel Invalid Configuration / SSL issues; do not.
3. **Overwrite zone** scripts that replace entire Hostinger/CF zone — historical scripts under `apps/web/scripts/` can wipe mail if misused; **do not run** for this migration.

---

## Conclusion

Optional alignment of **www → project `vercel-dns-017` CNAME** and/or keeping/changing apex **A** records is **email-safe and Paddle-safe** only when mail and verification TXT/MX records are left exactly as audited.
