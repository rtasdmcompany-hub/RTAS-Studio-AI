# Dashboard product spec

**Route:** `/profile`  
**Component:** `apps/web/src/components/profile/ProfileClient.tsx`

## Sections

1. **Welcome** (first visit / `?welcome=1`) — dismissible guidance
2. **Hero** — plan tier, greeting, primary CTA, continue draft
3. **Status cards** — Credits · Generation queue · Notifications
4. **Quick actions** — New video · Library · Upgrade · Pricing · Guide · Help
5. **Recent projects** — drafts + recent Studio work
6. **Activity** — job timeline (EmptyState when empty)
7. **Account / plans** — identity + inline checkout
8. **Library gallery** — finished assets

## First-time vs returning

| Signal | First-time |
|--------|------------|
| No draft, no projects, no jobs | Yes |
| Trial unused + no subscription | Yes |

## Copy principles

- One job per section
- No clutter badges in hero
- Errors use `Alert` with dismiss
- Empty states use `@rtas/ui` `EmptyState` with a single CTA
