# RTAS Studio AI — SEO Master Plan

**Classification:** Marketing / SEO  
**Phase:** 12 · Sprint 5  
**Product:** https://rtasstudio.com  
**Integrity:** Keyword clusters and playbooks only. No claimed rankings, traffic, or backlink counts.

Cross-links: [`CONTENT_STRATEGY.md`](CONTENT_STRATEGY.md) · `apps/web/src/lib/site-metadata.ts` · `apps/web/src/app/sitemap.ts` · `apps/web/src/app/robots.ts`

---

## 1. SEO objectives

1. Rank for **high-intent** queries around AI video studio, music video AI, commercial AI video, and transparent credit pricing — over time, measured honestly.  
2. Ensure technical foundations: crawlability, canonicals, metadata, sitemap, HTTPS, www→apex.  
3. Build topical authority via content clusters without fake link schemes.  
4. Protect brand SERP for “RTAS Studio AI” and operator entity queries.

---

## 2. Technical SEO (current baseline)

| Item | Status (audit) | Notes |
|------|----------------|-------|
| HTTPS / canonical host | Pass | `rtasstudio.com`; www → apex (middleware + next.config) |
| `metadataBase` + per-page `buildPageMetadata` | Pass | Titles, descriptions, OG, Twitter, canonicals |
| `robots.ts` | Pass | Index marketing; protect private areas as configured |
| `sitemap.ts` | Pass | Core marketing/help/legal URLs; no `/studio` (auth) |
| Structured data | Partial | Breadcrumbs/FAQ on key pages; expand Product/Offer carefully with true prices |
| Core Web Vitals | Partial | Monitor in Search Console — do not invent scores |
| `/contact` | Fixed Sprint 5 | 301 → `/help/contact` |
| Image SEO | Partial | OG image present; alt text hygiene ongoing |
| International SEO | Partial | `en_US` primary; hreflang deferred until true locales |

**Engineering hygiene checklist (ongoing):**

- Unique title/description per indexable page.  
- No soft-404 marketing stubs without clear next CTA.  
- Avoid duplicate plan-name confusion (canonical Tester/Standard/Premium 4K).  
- Keep legal pages indexable (Paddle MoR expectation).

---

## 3. On-page SEO

| Page | Primary intent | Must include |
|------|----------------|--------------|
| `/` | Brand + category | Brand hero, CTA Studio/Pricing, credit truth |
| `/pricing` | Commercial intent | Tester/Standard/Premium prices, FAQ schema |
| `/features` | Capability compare | Plan matrix with canonical names |
| `/showcase` | Visual proof | Real showcase media |
| `/how-to-use` | Tutorial intent | Steps + export honesty (no free trial myth) |
| `/blog` | Discovery hub | Links to deep content; evolve to articles |
| `/about` | Entity / trust | Operator, mission |
| `/help/*` | Support intent | Contact, FAQ, billing |
| Legal suite | Compliance / trust | Terms, Privacy, Refund, Cookies, AI Policy, Trust & Safety |

H1 = one clear topic. Internal links from blog/help → pricing/features. CTA language matches pricing truth.

---

## 4. Keyword clusters (planning — not claimed ranks)

| Cluster | Example intents | Target URL(s) |
|---------|-----------------|---------------|
| Brand | RTAS Studio AI, RTAS Digital Marketing | `/`, `/about` |
| AI video studio | AI video studio, AI video generator commercial | `/`, `/features` |
| Music video | AI music video, AI song video | `/showcase`, `/how-to-use` |
| Pricing / credits | AI video pricing per second, AI video credits | `/pricing` |
| Identity | Identity preservation video, authorized likeness AI | `/features`, `/trust-safety`, `/ai-policy` |
| How-to | How to make AI commercial, AI video workflow | `/how-to-use`, `/blog` |
| Billing support | Paddle RTAS billing, cancel subscription | `/help/billing`, `/refund` |

**Negative keywords / avoid:** deepfake, unauthorized face swap, free unlimited AI video (misleading).

---

## 5. Content SEO

- Map each priority topic in [`CONTENT_STRATEGY.md`](CONTENT_STRATEGY.md) to one primary URL.  
- Prefer updating living product pages over thin doorway pages.  
- Comparison content: honest category education — no “we beat X on every benchmark” without evidence.

---

## 6. Internal linking

**Hub pages:** Home, Pricing, Features, How-to-use, Help, Blog.  
**Spoke pages:** FAQ, Billing, Changelog, Trust, AI Policy, Showcase categories.

Rules:

- Every blog item links to ≥1 conversion page (Pricing or Studio via auth).  
- Footer uses `site-links.ts` (single source of truth).  
- Contact CTAs → `/help/contact` (and `/contact` redirect).

---

## 7. Backlinks (ethical)

| Tactic | Allowed | Disallowed |
|--------|---------|------------|
| Genuine guest posts / tutorials | Yes, disclosed | Paid link farms |
| Partner / agency mentions | After real relationship | Invented logos |
| Directories | Selective, relevant | Spam submissions |
| Digital PR | Real launches / policies | Fake news |

Track referring domains in Search Console when available — leave values blank until measured.

---

## 8. Image & video SEO

- Descriptive filenames and alt text for marketing images.  
- OG image: `/og-image.png` (1200×630).  
- Showcase videos: provide context on page; consider VideoObject schema only when accurate.  
- YouTube: optimize titles/descriptions with plan truth; link to rtasstudio.com.

---

## 9. International SEO

- Primary market language: English (`en_US`).  
- Do not add hreflang until localized pages exist.  
- MoR checkout may show local currency — pricing pages state USD list prices as source of truth.

---

## 10. Measurement (formulas only)

| Metric | Formula / source |
|--------|------------------|
| Organic sessions | Analytics (when configured) |
| Rankings | Search Console queries — observed only |
| CTR | `clicks / impressions` (GSC) |
| Index coverage | GSC coverage report |
| Assisted signups | Attribution model TBD — do not invent |

Fill values only from live tools. See [`MARKETING_KPI_FRAMEWORK.md`](MARKETING_KPI_FRAMEWORK.md).
