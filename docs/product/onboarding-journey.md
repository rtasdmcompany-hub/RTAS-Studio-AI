# Onboarding journey

**Goal:** A first-time user understands RTAS Studio AI within **60 seconds**.

## Flow

```
Signup → Email verify → Sign in
       → /profile?welcome=1 (Dashboard welcome strip)
       → Studio (first render)
       → Library + credits on Dashboard
```

## Implementation (no redesign)

| Step | Behavior |
|------|----------|
| Default auth callback | `/profile?welcome=1` (`AuthFlowGuard`, `AuthForm`, header auth links) |
| Welcome strip | `DashboardWelcome` — 3 steps, dismissible (`localStorage`) |
| First-time hero | “Create your first video” + “60-second guide” |
| Check-email | Points to dashboard sign-in + how-to-use |
| Quick actions | Product guide + Help Center |

## Success criteria

- [ ] User can name what Studio does
- [ ] User knows credits = seconds
- [ ] User knows where results appear (Dashboard library)
- [ ] User can find Help without hunting

## Do not

- Force multi-page modal tours that block creation
- Redirect returning users away from Studio when they deep-link `/studio`
