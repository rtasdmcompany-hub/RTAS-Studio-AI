# Release notes

## Unreleased / RC — Productization (2026-07)

### Product

- Post-auth landing defaults to Dashboard with welcome guidance (`?welcome=1`)
- Dismissible Dashboard welcome strip (60-second clarity)
- Help Center (`/help`) and Feedback (`/feedback`) Customer Success surfaces
- Header/footer navigation: Dashboard, Help
- About page differentiated for brand trust (no duplicate landing workflow)
- Activity empty state uses shared `EmptyState`

### Docs

- `docs/product/*` — product, onboarding, dashboard, FAQ, support
- `docs/developer/*` — API, troubleshooting
- `docs/marketing/*` — features & messaging
- `docs/launch/*` — investor/executive/sales/checklists
- Product Readiness Report

### Security / engineering (prior)

- Enterprise hardening already on `master` (rate limits, fail-closed webhooks, etc.)

## Known deferred

- Production domain, Paddle secrets, Resend domain, public GPU URL (external)
- Knowledge Base / video tutorials / community (placeholders on Feedback page)
