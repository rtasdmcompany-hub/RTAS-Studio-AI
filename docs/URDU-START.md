# RTAS Studio AI — Aap ke liye shuruati guide (Roman Urdu)

> **Note (2026-07):** Yeh document purana hai (pricing/trial/stack). Current product guide: in-app `/how-to-use` aur `/help`. English product docs: `docs/product/`.

## Kya ban chuka hai (pehla version)

1. **Website (Desktop + Mobile browser)** — `apps/web`
   - Prompt → Video aur Image → Video modes
   - Categories: Song, Islamic, Business, Cartoon, Story, Podcast
   - Har category ke apne boxes (baqi band)
   - Real Face / Avatar / Cartoon
   - Pehli video **30 second free**
   - Free khatam → **Subscribe** popup + **Skip for next time** (watermark, download nahi)
   - Built-in **video player** + center logo watermark (35% opacity)
   - Profile, credits, Terms & Conditions (RTAS DIGITAL MARKETING COMPANY)

2. **Mobile app skeleton** — `apps/mobile` (Play Store / App Store ke liye Expo)

3. **Shared rules** — credits ($89, 500 credits, 50 per 5 min) sab jagah same

## Abhi demo mode

Jab tak aap **Runway / Kling** API keys nahi dalte, sample video chalegi (testing). Asal AI video ke liye `apps/web/.env.local` bharein.

## Aap ab kya karein (order)

### Step 1 — Software install

| # | Cheez | Link |
|---|--------|------|
| 1 | Node.js 20 LTS | https://nodejs.org |
| 2 | Git | https://git-scm.com/download/win |

### Step 2 — Project chalana

PowerShell:

```powershell
cd "H:\PERSONAL\RTAS Digital Marketing Company\RTAS Softwear\RTAS Studio AI\RTAS Studio AI"
npm install
npm run dev
```

Browser: **http://localhost:3000** → **Open Studio**

### Step 3 — Logo

Apna logo file yahan rakhein:

`apps/web/public/logo.png`

### Step 4 — Accounts (business)

- **Stripe** — $89/month subscription (international cards)
- **JazzCash / EasyPaisa Merchant** — Pakistan
- **Runway + Kling** — video quality (real face ke liye Kling Character ID best)

Poori list: `docs/SETUP-DOWNLOADS.md`

## Competitors se seekha kya?

Hum ne **Runway, Kling, Pika** jaisi products study ki — un ka **secret code copy nahi** kiya (ye illegal hota). International product **un ki official APIs** use karta hai + aap ka apna design, billing, watermark, categories.

| Feature | RTAS Studio AI approach |
|---------|-------------------------|
| Professional ads | Runway Gen-4 API |
| Real face lock | Kling Character ID + reference photo |
| Long / motion | Kling |
| Cartoon / social | Fal / Replicate |

## Agle phases (developer ke sath)

1. Supabase/Firebase — cloud profile + videos save
2. Stripe live + PK payment webhooks
3. FFmpeg server — watermark video file par burn
4. App Store / Play Store publish
5. Content moderation (Islamic / kids)

## Support email

Terms mein `support@rtasdigital.com` — apna asal email daal dein jab ready hon.

---

**RTAS DIGITAL MARKETING COMPANY** · **RTAS GROUP OF COMPANIES** · **RTAS STUDIO AI**
