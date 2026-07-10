# Empty, success, and error states

## Standard

Use `@rtas/ui` `EmptyState` with:

- Clear **title**
- One **description** sentence
- Optional single **action** (`actionHref` / `actionLabel`)

## Inventory

| Surface | Empty | Success | Error |
|---------|-------|---------|-------|
| Dashboard projects | EmptyState → Studio | Continue draft card | Sync `Alert` |
| Dashboard activity | EmptyState → how-to-use | Timeline items | — |
| Gallery | EmptyState | Cards | Gallery `Alert` |
| Auth check-email | — | Resend notice | Delivery `Alert` |
| Share missing | EmptyState | Public player | 404 |
| Studio toasts | — | `StudioToast` | Pipeline customer copy |

## Error tone

- Customer-safe by default
- Owner diagnostics only when `NEXT_PUBLIC_OWNER_EMAILS` matches
- Never dump stack traces in UI
