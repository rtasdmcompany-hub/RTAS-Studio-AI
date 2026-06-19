# Payment webhooks — Paddle & Lemon Squeezy

RTAS Studio AI uses a **Merchant of Record** (MoR) for international tax compliance and payouts (including Pakistan bank configuration in the MoR dashboard).

## Endpoints

| Provider | Webhook URL |
|----------|-------------|
| Paddle | `POST /api/webhooks/paddle` |
| Lemon Squeezy | `POST /api/webhooks/lemon-squeezy` |

## On successful payment

Webhooks call `applyPremiumFromWebhook()` which:

1. Sets `tier` → `"premium"`
2. Sets `subscriptionActive` → `true`
3. Credits **500** tokens (`MONTHLY_CREDITS`)
4. Stores `externalCustomerId` / `externalSubscriptionId`

Profiles are persisted in `.data/profiles.json` (replace with Supabase/Postgres in production).

## Checkout custom data

Pass `user_id` in checkout so webhooks map to the correct account:

- **Paddle:** `custom_data.user_id`, `custom_data.email`
- **Lemon Squeezy:** `checkout[custom][user_id]`

## Environment

See `apps/web/.env.example`:

- `NEXT_PUBLIC_PAYMENT_PROVIDER=paddle` or `lemon_squeezy`
- `PADDLE_WEBHOOK_SECRET` / `LEMONSQUEEZY_WEBHOOK_SECRET`

## Client sync

After checkout redirect (`/studio?payment=success`), the app calls `GET /api/user/subscription?userId=...` to merge server state into localStorage.

## Config API

`GET /api/payments/config` — returns active provider and webhook paths.
