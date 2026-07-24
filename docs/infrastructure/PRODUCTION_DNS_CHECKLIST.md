# Production DNS / Domain Checklist — rtasstudio.com

Use before and after any manual Cloudflare DNS edit. Check items in order.

---

## A. Backup (before any change)

- [ ] Export / screenshot Cloudflare DNS Records page (all 9+ records)
- [ ] Confirm this repo’s snapshot matches live: `docs/infrastructure/DNS_AUDIT_BEFORE.md`
- [ ] Confirm Resend dashboard shows domain **Verified**
- [ ] Confirm no orange cloud on apex/www

---

## B. Propagation (after change)

- [ ] `dig NS rtasstudio.com` → Cloudflare NS only
- [ ] `dig A rtasstudio.com` → expected A value(s)
- [ ] `dig CNAME www.rtasstudio.com` → expected CNAME
- [ ] `dig MX rtasstudio.com` → Forward Email unchanged
- [ ] `dig TXT rtasstudio.com` → SPF + forward-email unchanged
- [ ] `dig TXT resend._domainkey.rtasstudio.com` → DKIM present
- [ ] Wait ≥ TTL (300s) + spot-check from phone LTE

---

## C. SSL / Vercel

- [ ] Vercel → Project → Domains: `rtasstudio.com` Valid / not misconfigured
- [ ] `www.rtasstudio.com` Valid (redirect OK)
- [ ] HTTPS padlock on apex and www
- [ ] No Cloudflare 526 / browser NET::ERR_CERT_*

---

## D. Application surfaces

- [ ] Homepage `https://rtasstudio.com`
- [ ] Studio `https://rtasstudio.com/studio` (auth gate OK)
- [ ] API ready `https://rtasstudio.com/api/ready` → 200
- [ ] Health `https://rtasstudio.com/api/health` (expect healthy)
- [ ] Login / Google OAuth complete round-trip
- [ ] Dashboard / profile loads for a test user

---

## E. Payments (Paddle)

- [ ] Pricing page loads
- [ ] Checkout opens (sandbox or live per env)
- [ ] Webhook delivery recent success in Paddle + app logs
- [ ] No DNS dependency beyond HTTPS hostname

---

## F. Email

- [ ] Resend still **Verified**
- [ ] Send test transactional (auth / password reset) from production
- [ ] Inbound test to `support@rtasstudio.com` (or `info@`) arrives via Forward Email → Gmail
- [ ] If DMARC added: `dig TXT _dmarc.rtasstudio.com` shows expected policy

---

## G. Sign-off

| Gate | Pass? | Initials / date |
|------|-------|-----------------|
| Web DNS | | |
| SSL | | |
| App | | |
| Paddle | | |
| Email | | |
| Rollback path reviewed | | |
