# Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| CI lint: cannot find `typescript` | Hoisting | Root `devDependencies.typescript` present |
| `/api/ready` 503 | Missing `FASTAPI_URL` / Paddle secret | Fill Vercel env from `.env.production.example` |
| Google login fails | Redirect URI mismatch | Match `GOOGLE_OAUTH_*` to domain |
| Emails only to owner | Resend sandbox from | Verify domain + `EMAIL_FROM` |
| Generation fails | No `FASTAPI_URL` / fal credits | Set worker URL + `FAL_KEY` |
| Checkout no-op | Missing checkout URLs | Set `NEXT_PUBLIC_PADDLE_*_CHECKOUT_URL` |
| Dashboard empty forever | First-time user | Expected until first Studio session |

Ops runbooks: [OPERATIONS.md](../OPERATIONS.md) · [RECOVERY.md](../RECOVERY.md)
