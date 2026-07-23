# RTAS Studio AI — Enterprise Brand Guide

**Phase:** 13 · Sprint 1  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Purpose:** Single reference for tone, type, spacing, buttons, icons, illustration, and imagery for international SaaS marketing materials.  
**Status labels:** **Verified** = live in design tokens / shipped site · **Proposed** = recommended, not yet shipped as a separate system.

**Token sources (Verified):**

- `packages/design-tokens/css/tokens.css`
- `packages/design-tokens/src/typography.ts`
- `packages/design-tokens/src/spacing.ts`
- `packages/design-tokens/src/colors.ts`
- Web font wiring: `apps/web/src/app/layout.tsx`
- Prior guidelines: `docs/branding/BRAND_GUIDELINES.md`

---

## 1. Brand system snapshot

| Element | Spec | Status |
|---------|------|--------|
| Primary product name | RTAS Studio AI | Verified |
| Operator credit | RTAS Digital Marketing Company | Verified |
| Visual identity | Ink + gold + lavender on cinematic dark surfaces | Verified |
| Logo (SVG) | `apps/web/public/logo.svg` | Verified |
| OG image | `apps/web/public/og-image.png` | Verified |
| Group mark | `apps/web/public/rtas-group-logo.png` when present | Verified (when file present) |
| Light-mode brand kit | Dedicated light lockups | Proposed |

---

## 2. Tone of voice

| Trait | Expression | Status |
|-------|------------|--------|
| Craft-led | Cinema and commercial outcomes over prompt gimmicks | Verified (messaging docs + site) |
| Trust-first | Authorized Identity Preservation; never deepfake/face-swap marketing | Verified |
| Transparent | 1 credit = 1 second; published tiers | Verified |
| International SaaS | Calm, precise English; global buyer framing | Verified |
| Operator-real | Built inside a marketing company | Verified |

**Preferred words (Verified):** studio · credits · seconds · authorized · Identity Preservation · commercials · music videos · compose · render · publish · Merchant of Record (state honestly).

**Banned in marketing (Verified policy):** deepfake · face-swap (as a feature) · “undetectable” · fake user counts · “#1” · “guaranteed Hollywood quality” · invented awards/logos.

**Register:** Confident and cinematic — not hype-bro, not whitepaper-dense, not purple-glow AI cliché for its own sake.

---

## 3. Typography

### Verified (live)

| Role | Spec |
|------|------|
| Primary sans | **Inter** via `next/font/google` → `--font-inter` |
| Token alias | `--ds-font-sans: var(--font-inter, "Inter"), system-ui, …` |
| Mono | `--ds-font-mono` / `fontFamily.mono` |
| Weights | 400 · 500 · 600 · 700 |

### Scale (Verified token names)

From `typography.ts` / CSS tokens: `xs` 0.75rem · `sm` 0.875rem · `base` 1rem · `lg` 1.125rem · `xl` 1.25rem · `2xl` 1.5rem · `3xl` 1.875rem · `4xl` 2.25rem · `5xl` 3rem · `6xl` 3.75rem.

### Presets (Verified in tokens)

| Preset | Use |
|--------|-----|
| `display` / `h1` | Hero and page titles |
| `h2`–`h4` | Section hierarchy |
| `body` / `bodySm` | Supporting copy |
| `eyebrow` / `caption` | Labels, trust lines |

### Proposed

A distinctive **display face for hero headlines only**, still paired with Inter for UI/body. Until shipped in `layout.tsx`, **Inter remains the only official typeface**. Do not invent a custom serif as “current brand type.”

---

## 4. Color (Verified accents)

| Name | Example hex | Role |
|------|-------------|------|
| Lavender 500 | `#a594fd` | Primary CTA / link accent |
| Lavender 400 | `#b8abff` | Hover |
| Gold 500 | `#c9a227` | Brand metal / premium accent |
| Gold 400 | `#e8c547` | Gradients / highlights |
| Ink 950–800 | `#09090b` → `#12141f` | Backgrounds / panels |
| White / zinc | `#ffffff` / `#f4f4f5` | Primary text |

**Identity rule (Verified):** RTAS = **ink + gold + lavender**. Avoid defaulting collateral to generic purple-on-white SaaS templates or warm-cream / terracotta clichés.

**Light mode campaigns:** Proposed until approved tokens/assets exist.

---

## 5. Spacing

### Verified scale (`packages/design-tokens/src/spacing.ts`)

| Token key | Value |
|-----------|-------|
| 1 | 0.25rem |
| 2 | 0.5rem |
| 3 | 0.75rem |
| 4 | 1rem |
| 6 | 1.5rem |
| 8 | 2rem |
| 10 | 2.5rem |
| 12 | 3rem |
| 16 | 4rem |
| 20 | 5rem |
| 24 | 6rem |
| 32 | 8rem |

### Layout recommendations (Proposed, based on live marketing patterns)

| Context | Guidance |
|---------|----------|
| Section vertical rhythm | Prefer 4–8rem between major marketing sections |
| CTA group gap | 0.75–1.25rem between primary and secondary |
| Card / panel padding | 1.5–2rem interior when panels are used |
| Clear space around logo | ≥ ~0.25× logo height |

---

## 6. Button hierarchy

### Verified variants (`packages/ui` Button / ButtonLink)

| Priority | Variant | Use |
|----------|---------|-----|
| **Primary** | `lavender` / `lavender-lg` | Main conversion (Start creating, Open Studio, Compare plans) |
| **Secondary** | `ghost` | Pricing, showcase, enterprise, feature links |
| **Supporting** | `primary` / `secondary` / `ui-primary` / `ui-ghost` | App chrome consistency |
| **Commerce** | `paywall*` | Checkout / subscribe contexts only |
| **Destructive** | `asset-danger` | Asset deletion — never marketing CTAs |

### Sizes (Verified)

`sm` · `md` · `lg` — apply consistently; hero primary prefers `lavender-lg`.

### Hierarchy rules (Proposed for collateral; mirrors live site)

1. One primary CTA per viewport section.  
2. Secondary always ghost/outline on dark glass — never compete with lavender fill.  
3. Do not stack three equally weighted filled buttons in a hero.  
4. Paywall variants stay inside billing UI — not homepage hero.

---

## 7. Icon style

| Rule | Status |
|------|--------|
| Prefer simple line or minimal filled glyphs consistent with dark UI chrome | Proposed (codify; sample live studio icons) |
| Stroke weight optically ~1.5–2px at 24px | Proposed |
| Corner radius soft, not playful sticker | Proposed |
| Color: muted white / lavender accent; gold sparingly for premium states | Proposed aligned to tokens |
| Never use deepfake / face-mash iconography | Verified policy |
| Never invent “certified” shield badges implying awards | Verified policy |

---

## 8. Illustration policy

| Do | Don’t | Status |
|----|-------|--------|
| Abstract cinematic frames, waveform/lyric motifs, studio pipeline diagrams | Cartoon mascots that undercut premium studio positioning | Proposed |
| Gold/lavender on ink geometric accents | Stock “robot with clapperboard” clichés as hero | Proposed / Verified imagery preference |
| Illustrate **authorized** talent silhouettes only with clear rights framing | Face-swap / impersonation visuals | Verified |
| Label conceptual art as conceptual | Present mock metrics dashboards as real traction | Verified |

**Default preference (Verified):** Real product UI and showcase video over invented illustration systems.

---

## 9. Image & motion usage

| Asset type | Guidance | Status |
|------------|----------|--------|
| Showcase MP4s | `apps/web/public/showcase/*.mp4` — primary motion truth | Verified |
| Rotating background video | Part of live marketing experience | Verified |
| Product screenshots | Crop cleanly; no fake filled customer tables | Verified policy |
| Identity visuals | Imply authorized use only | Verified |
| Customer logos | Only after written approval | Verified |
| Stock photography | Last resort; prefer product/output | Proposed for campaigns |

**Motion principle (Proposed, matches site intent):** 2–3 intentional motions for presence — not noise, not endless purple glow particles.

---

## 10. Logo usage (Verified)

- Clear space ~0.25× height.  
- Do not stretch, recolor arbitrarily, or add unauthorized AI sparkle stickers.  
- On dark cinematic backgrounds, use existing SVG as-is.  
- Light-background lockups: Proposed — create verified variants before shipping.

---

## 11. Enterprise collateral checklist

When building decks, one-pagers, or partner sheets:

- [ ] Product name = RTAS Studio AI  
- [ ] Operator cited where legal/investor context requires  
- [ ] Pricing matches shared constants (Tester / Standard / Premium)  
- [ ] Authorized Identity Preservation language — never deepfake  
- [ ] Colors from tokens (ink / gold / lavender)  
- [ ] Type = Inter unless a Proposed display face is approved  
- [ ] No invented customers, rankings, certifications, awards  
- [ ] MoR / payment status stated only as known (historically Paddle; may migrate)

---

## Related

[`brand-positioning.md`](./brand-positioning.md) · [`mission-vision.md`](./mission-vision.md) · `docs/branding/BRAND_GUIDELINES.md`
