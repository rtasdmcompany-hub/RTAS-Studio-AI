# Email Security Audit — rtasstudio.com

**Audit date:** 2026-07-24  
**Sources:** Public DNS (Google DoH) + Resend API GET (verified status)

---

## Summary

| Control | Status | Risk |
|---------|--------|------|
| SPF (apex) | **Present** | Low |
| SPF (`send.`) | **Present + Resend verified** | Low |
| DKIM (Resend) | **Present + verified** | Low |
| DMARC | **Missing** | Medium (spoofing / reporting gap) |
| Inbound MX | Forward Email present | OK (delivery path) |

---

## SPF

### Apex (`rtasstudio.com` TXT)

```
v=spf1 include:spf.forwardemail.net include:amazonses.com ~all
```

- Soft fail (`~all`) — appropriate for gradual enforcement
- Covers Forward Email + Amazon SES include used by Resend pathing

### Sending subdomain (`send.rtasstudio.com` TXT)

```
v=spf1 include:amazonses.com ~all
```

Resend API: **verified**

---

## DKIM

Host: `resend._domainkey.rtasstudio.com`  
Type: TXT (`p=MIGfMA0…`)  
Resend API: **verified**

Outbound from Resend should authenticate under current keys.

---

## DMARC — Missing (action recommended)

`_dmarc.rtasstudio.com` → **no TXT** (DoH Status 3).

### Why add it

- Tells receivers how to handle SPF/DKIM failures
- Enables aggregate reports (`rua`) for spoof monitoring
- Industry baseline for production domains sending auth mail

### Recommended first record (monitor-only)

Add TXT at Cloudflare:

| Field | Value |
|-------|-------|
| Type | TXT |
| Name | `_dmarc` |
| Content | `v=DMARC1; p=none; rua=mailto:admin@rtasstudio.com; fo=1` |
| Proxy | DNS only (TXT) |

Notes:

- `p=none` = monitor only; does **not** quarantine/reject
- Ensure `admin@rtasstudio.com` is a working Forward Email alias (already in alias map)
- After 2–4 weeks of clean reports, consider `p=quarantine` then `p=reject` (separate change)

### Do not

- Jump straight to `p=reject` without report review
- Remove SPF/DKIM while adding DMARC

---

## Alignment with web DNS migration

Adding DMARC is **independent** of Vercel A/CNAME targets and is the only email DNS change recommended in this audit package.
