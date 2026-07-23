# Help Center

**Route:** `/help`  
**FAQ:** `/help/faq`  
**Hub:** `/success`

---

## Categories

1. Account  
2. Billing  
3. Credits  
4. Video Generation  
5. Templates  
6. AI Models  
7. Enterprise  
8. API  
9. Security  
10. Technical Issues  

Source of truth: `apps/web/src/lib/customer-success/help-kb.ts`

## Search

Client-side search filters title, body, tags, and category. Empty results point users to `/tickets`.

## Related pages

| Page | Purpose |
|------|---------|
| `/help/billing` | Plans & credits |
| `/help/troubleshooting` | Common fixes |
| `/help/changelog` | Release notes |
| `/help/contact` | Email / Discord |
| `/how-to-use` | Getting started |
| `/docs` | Developer docs |

## SEO

`/help`, `/help/faq`, and `/success` are in `sitemap.ts`. Ticket/retention/health routes are `noIndex`.
