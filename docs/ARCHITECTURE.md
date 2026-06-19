# RTAS Studio AI — Architecture

## Important (legal & technical)

We **do not copy** Runway/Kling/Pika proprietary source code. International products integrate **licensed APIs** and follow each provider's Terms of Service. RTAS owns the **UX, billing, credits, watermark policy, and category workflows**.

## Stack

```
┌─────────────────────────────────────────────────────────┐
│  Web (Next.js 14)  │  Mobile (Expo React Native)        │
│  Responsive UI     │  Same API + shared types            │
└──────────────┬──────────────────────────────────────────┘
               │ REST / tRPC (future)
┌──────────────▼──────────────────────────────────────────┐
│  API Routes (Next.js)                                    │
│  • Auth session                                          │
│  • Credits ledger                                        │
│  • Generation queue                                      │
│  • Stripe webhooks                                       │
│  • PK payment webhooks                                   │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────┐  ┌────────────────────────────┐
│  Video orchestration     │  │  Storage (S3/R2)            │
│  Runway / Kling / Fal    │  │  User videos + thumbnails   │
└──────────────────────────┘  └────────────────────────────┘
```

## Generation pipeline

1. User selects **mode** (prompt | image) + **category** + **visual style** (real | avatar | cartoon).
2. Category-specific fields validated (`packages/shared`).
3. **Credit check**: free 30s once → else subscription or skip-preview path.
4. Job queued → provider API (style routes to best model).
5. **Real face**: require reference image; use identity-preserving provider flags; post-check disclaimer in UI.
6. Output → storage → built-in player URL.
7. Download gated: `canDownload = subscribed && !previewOnly`.

## Credit math

- `creditsForDuration(seconds) = ceil(seconds / 300) * 50` (50 per 5 min block)
- Monthly grant: 500 on successful invoice
- Expiry: end of `billingPeriodEnd`
- Resubscribe before expiry: `newBalance = remaining + 500`

## Watermark (preview / no subscription)

Center logo PNG, opacity 0.30–0.40, CSS overlay on player + burned in on export when using FFmpeg worker.

## Categories → fields

Defined in `packages/shared/src/categories.ts` — single source for web + mobile.

## Compliance

- Terms: RTAS DIGITAL MARKETING COMPANY, RTAS GROUP OF COMPANIES
- User warrants rights to uploads; AI output subject to provider policies
- Islamic / kids content: moderation flags (future: human review queue)
