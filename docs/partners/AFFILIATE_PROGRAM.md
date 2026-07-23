# RTAS Studio AI — Affiliate Program

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company  
**Status:** Applications open for review · **Payouts NOT LIVE** until configured  
**Public page:** `/affiliate` · Dashboard: `/affiliate/dashboard` (auth)

---

## Integrity

- No fabricated affiliates, commissions, clicks, conversions, or revenue.
- Commission bands on `/affiliate` are **placeholders** and must stay labeled as such.
- Do not market live earnings while `AFFILIATE_PAYOUTS_LIVE=false` (default).

---

## Program summary

| Element | Value |
|---------|--------|
| Cookie / attribution window | `AFFILIATE_COOKIE_DAYS` (default **30**) |
| Payouts live gate | `AFFILIATE_PAYOUTS_LIVE` (default **false**) |
| Min payout (placeholder) | `AFFILIATE_MIN_PAYOUT_USD` (default **$50**) |
| Payout schedule (placeholder) | Monthly · Net-`AFFILIATE_PAYOUT_NET_DAYS` (default **30**) |
| Pricing truth | Tester $5 · Standard $89/mo · Premium $249/mo · 1 credit = 1 second |

---

## Application flow

1. Applicant submits `/affiliate` form → `POST /api/affiliate/apply`.
2. Record stored in `AffiliateApplications` (requires `DATABASE_URL`).
3. Notification email to `contact@rtasstudio.com` when Resend/SMTP configured.
4. If signed in, a pending `AffiliateAccount` with referral code stub is created.
5. Dashboard shows real zeros until attribution is connected.

---

## Forbidden promotions

- Unauthorized likeness / deepfake positioning  
- Fake unlimited free credits  
- Trademark bidding without approval  
- Incentivized fake signups  

Identity Preservation remains **authorized-content only**.

---

## Related docs

- [`COMMISSION_STRUCTURE.md`](./COMMISSION_STRUCTURE.md)  
- [`MARKETING_RESOURCES.md`](./MARKETING_RESOURCES.md)  
- [`../growth/AFFILIATE_PROGRAM_STRATEGY.md`](../growth/AFFILIATE_PROGRAM_STRATEGY.md) (strategy; Planned)

---

*Not a live earnings offer until payouts are enabled and confirmed in writing.*
