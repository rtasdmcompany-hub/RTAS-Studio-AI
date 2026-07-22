# RTAS Studio AI — Product One-Pager

**Enterprise brochure** · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company · Operating from Pakistan  
**Legal:** Documentation v1.1 APPROVED · Paddle AUP–aligned positioning  
**Audience:** Marketing leads, producers, IT/security reviewers, procurement

---

## Positioning

RTAS Studio AI is an **AI video studio SaaS** for text-to-video and image-to-video across music videos, commercials, social content, and animation. **Identity Preservation** supports likeness continuity for **original, licensed, owned, or authorized** content only—not unauthorized impersonation or face-swap marketing.

---

## Features

| Capability | Description |
|------------|-------------|
| Prompt-to-Video | Generate from natural-language creative briefs |
| Image-to-Video | Animate or extend from reference stills |
| Category workflows | Commercials, social, music video, animation presets |
| Identity Preservation | Authorized identity consistency under AI Policy |
| Credit metering | **1 credit = 1 second** of generated video |
| Studio + Dashboard | Generate, queue, library, billing status |
| Auth | Email verification + Google OAuth |
| Share & library | Project continuity and share flows |
| Help & feedback | Help Center + human support path |
| MoR checkout | **Paddle** (live checkout/domain may still be pending — honest) |

---

## AI Workflow

1. Sign in and open **Studio**.  
2. Choose **prompt** or **image** mode; select category and style.  
3. System validates inputs and checks **credits**.  
4. Job enters the generation queue; progress/ETA visible in UI.  
5. Fal GPU pipeline renders; result lands in library with entitlement rules.  
6. Download / share per plan rights; iterate with remaining seconds.

Longer Standard/Premium outputs can be handled as segmented generation with stitch behavior where productized—buyers should validate current Studio behavior in a live demo.

---

## Security & Trust

**Verified posture highlights:**

- Session-protected Studio/profile surfaces; email verification on credential accounts  
- Secrets via environment configuration (not hardcoded)  
- Payment webhooks designed fail-closed when secrets missing  
- Upload validation and share URL controls documented in security runbooks  
- Public **Trust & Safety** and **AI Usage Policy** pages  
- Legal pack v1.1: Terms (incl. Acceptable Use), Privacy, Refund, Cookies  

Full packet: `docs/SECURITY.md` and legal pages on rtasstudio.com.

---

## Pricing

| Plan | Price | Credits | Notes |
|------|------:|--------:|-------|
| Tester | **$5** · 5 days | **30 seconds** | Evaluation / pipeline proof |
| Standard | **$89 / month** | **2,000 seconds** (~33 min) | Default commercial plan |
| Premium | **$249 / month** | **2,000 seconds** | Cinematic / 4K positioning |

**Verified:** Prices and credit pools match product constants.  
**MoR:** Paddle collects and invoices per legal; activation status should be confirmed at purchase time.

---

## Target Customers

Marketing agencies · Production studios · Creators · YouTubers · Ad agencies · Education media teams · Corporate communications · Government digital teams (policy-constrained) · Media publishers · E-commerce brands  

Profiles: [Target-Customer-Profiles.md](./Target-Customer-Profiles.md)

---

## Competitive Advantages

- Integrated studio SaaS vs. single-model sandboxes  
- Transparent second-based economics  
- Compliance-first Identity Preservation messaging  
- International MoR design (Paddle)  
- Documented enterprise ops (security, DR, architecture)  
- RTAS brand + digital marketing operator adjacency  

---

## Deployment

| Layer | Technology |
|-------|------------|
| Web | Next.js on **Vercel** |
| Data | **Prisma** → **Supabase** Postgres |
| API / workers | **FastAPI** GPU gateway |
| Render | **Fal** cloud GPU |
| Email | **Resend** |
| DNS | **Cloudflare** |
| Payments | **Paddle** MoR |

Customer deployment today is **multi-tenant cloud SaaS**. Private VPC / on-prem GPU is not claimed as a current SKU.

---

## API

Partner and automation API surfaces exist in engineering documentation (`docs/API.md`, developer docs). Enterprise buyers seeking programmatic generation should request current endpoint scope, auth model, and rate limits in a technical call—do not assume public unlimited API access from marketing alone.

---

## Support

| Channel | Use |
|---------|-----|
| Help Center | `/help` — guides, billing, troubleshooting |
| Contact | contact@rtasstudio.com (and Help contact flows) |
| Feedback | In-product / `/feedback` |
| Legal | Terms, Privacy, Refund, AI Policy, Trust & Safety |

Enterprise SLA tiers (response-time contracts) should be negotiated separately if required by procurement; not invented here.

---

## Call to action

1. Visit https://rtasstudio.com  
2. Start with **Tester ($5)** to validate quality on authorized assets  
3. Upgrade to **Standard** or **Premium** for monthly production volume  
4. Ask for security/legal packet and ROI model for stakeholder approval  

**ROI model:** [Enterprise-ROI-Calculator.md](./Enterprise-ROI-Calculator.md)  
**Executive brief:** [Executive-Summary.md](./Executive-Summary.md)
