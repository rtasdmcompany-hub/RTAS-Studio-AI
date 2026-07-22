# RTAS Studio AI — Brand Guidelines

**Classification:** Visual & verbal brand system  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Source of truth for colors/type:** Live design tokens in `packages/design-tokens/css/tokens.css` and web font wiring in `apps/web/src/app/layout.tsx`  
**Status labels:** **Current (live site)** · **Proposed** (not yet shipped)

---

## 1. Logo system

### Current assets (do not invent alternatives as “official”)

| Asset | Path | Use |
|-------|------|-----|
| Primary mark (SVG) | `apps/web/public/logo.svg` | Favicon / header mark / compact brand |
| Open Graph | `apps/web/public/og-image.png` | Social share previews |
| Group logo | `apps/web/public/rtas-group-logo.png` | Operator / ecosystem contexts when the file is present |
| Showcase video | `apps/web/public/showcase/*.mp4` | Product truth in motion |

**Logo SVG description (current):** Rounded square on ink (`#1a1d2e` → `#12141f`), gold play-triangle and “RTAS” wordmark using gold gradient `#e8c547` → `#c9a227`, gold stroke.

### Usage rules (current)

- Clear space: keep at least ~0.25× logo height of empty space around the mark.  
- Do not stretch, recolor arbitrarily, or add unauthorized “AI sparkle” stickers.  
- Prefer gold/lavender accents from tokens; do not replace the mark with deepfake-style face mashups.  
- On dark cinematic backgrounds (site default), use the existing SVG as-is.  
- On light backgrounds (**Proposed**): create a verified light-mode variant before shipping; do not invert casually in ads until a file exists.

### Lockups (**Proposed**)

| Lockup | Status |
|--------|--------|
| Mark + “RTAS Studio AI” wordmark horizontal | Proposed for press kit |
| Mark + “by RTAS Digital Marketing Company” | Proposed for legal/partner one-pagers |
| Monochrome gold-on-black / black-on-gold | Proposed |

---

## 2. Typography

### Current (live)

| Role | Spec |
|------|------|
| Primary UI / marketing sans | **Inter** via `next/font/google` → CSS variable `--font-inter` |
| Token alias | `--ds-font-sans: var(--font-inter, "Inter"), system-ui, -apple-system, BlinkMacSystemFont, sans-serif` |
| Mono (code / pipeline) | `--ds-font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace` |
| Weights in tokens | 400 normal · 500 medium · 600 semibold · 700 bold |

### Scale (current token names)

`--ds-text-2xs` 10px · `--ds-text-xs` 12px · `--ds-text-sm` 14px · `--ds-text-base` 16px · `--ds-text-lg` 18px · larger display sizes as used in marketing CSS.

### Proposed (optional future)

A distinctive display face for hero headlines only (still paired with Inter for body). Until chosen and shipped in `layout.tsx`, **Inter remains the only official typeface**. Do not claim a custom serif or obscure font as “current brand type.”

---

## 3. Color system

### Brand accents (current — from tokens)

| Name | Token | Hex | Role |
|------|-------|-----|------|
| Lavender (primary CTA / links accent) | `--ds-color-lavender-500` / `--rtas-lavender` | `#a594fd` | Buttons, accents, focus |
| Lavender hover | `--ds-color-lavender-400` | `#b8abff` | Hover states |
| Gold (brand metal) | `--ds-color-gold-500` / `--ds-accent` | `#c9a227` | Logo metal, premium accents |
| Gold bright | `--ds-color-gold-400` / `--ds-accent-2` | `#e8c547` | Gradients, highlights |
| Gold soft | `--ds-color-gold-300` | `#fde68a` | Soft highlights |

### Surfaces & text (current)

| Name | Token | Hex / value | Role |
|------|-------|-------------|------|
| Ink deep | `--ds-color-ink-950` | `#09090b` | Deepest background |
| Ink base | `--ds-color-ink-900` | `#0a0b10` | App background |
| Ink panel | `--ds-color-ink-800` | `#12141f` | Panels / logo fill |
| Ink elevated | `--ds-color-ink-650` | `#1a1d2e` | Elevated surfaces |
| Text primary | `--ds-color-white` / zinc-100 | `#ffffff` / `#f4f4f5` | Headings / body |
| Text muted | zinc-200 / zinc-300 | `#e4e4e7` / `#d4d4d8` | Secondary copy |
| Header chrome | — | `rgba(5, 5, 9, 0.92)` | Fixed premium header |

### Semantic (current)

| Role | Token family | Example |
|------|--------------|---------|
| Success | `--ds-color-green-500` | `#4ecb8c` |
| Danger | `--ds-color-red-500` | `#e85d5d` |
| Warning | amber family | `#f59e0b` |

### Gradients (current usage pattern)

- Gold → lavender cinematic accents appear in marketing CSS (e.g. gold-300 → accent-2 → violet).  
- Marketing comment in stylesheet: “RTAS gold + lavender premium.”  
- Avoid defaulting creative to generic purple-on-white SaaS clichés; RTAS identity is **ink + gold + lavender**.

### Light mode (**Proposed**)

Light surfaces and ink text are **not** the primary shipped marketing look. Any light campaign materials must be labeled Proposed until tokens and assets are approved.

---

## 4. Imagery & motion

### Current

- Prefer real product UI, studio outputs, and showcase videos over stock “robot holding film clapper” art.  
- Rotating / cinematic background video is part of the live site experience.  
- Identity-related visuals must imply **authorized** talent/brand use—never unauthorized face-swap marketing.

### Do / Don’t

| Do | Don’t |
|----|-------|
| Show commercials, music-video, animation outcomes | Market deepfakes or non-consensual likeness |
| Use gold/lavender on ink | Invent award badges or customer logos |
| Caption credits/pricing accurately | Imply unlimited free 4K cinema |
| Credit RTAS Studio AI clearly | Use competitor logos without permission |

---

## 5. UI chrome patterns (current)

- Primary CTA class pattern: lavender fill (`--rtas-lavender`) with dark ink text.  
- Ghost / secondary: translucent white borders on dark glass.  
- Header: fixed, blurred dark glass, gold/lavender accents for brand text.  
- Footer: international site footer with product + operator framing.

Contractors building decks should sample live pages at https://rtasstudio.com rather than inventing a second system.

---

## 6. Voice & microcopy

Align with [`MESSAGING_FRAMEWORK.md`](./MESSAGING_FRAMEWORK.md) and USP.

**Preferred words:** studio · credits · seconds · authorized · Identity Preservation · commercials · music videos · animation · Merchant of Record (Paddle) · Trust & Safety.

**Banned in marketing:** deepfake · face-swap (as a feature claim) · “undetectable” · fake user counts · “guaranteed Hollywood quality.”

---

## 7. File delivery checklist (future press kit)

**Current:** assets live in `apps/web/public/`.  
**Proposed package contents:** SVG + PNG @1x/@2x, OG, group logo, color PDF one-pager, voice card, AUP one-pager.

Until packaged, share individual verified files—do not fabricate a “Brand Book v1 PDF” filename as if it already exists.

---

## 8. Related documents

- [`BRAND_STRATEGY.md`](./BRAND_STRATEGY.md)  
- [`MESSAGING_FRAMEWORK.md`](./MESSAGING_FRAMEWORK.md)  
- Asset index pointer: [`business/branding/README.md`](../../business/branding/README.md)  
- Tokens: `packages/design-tokens/css/tokens.css`
