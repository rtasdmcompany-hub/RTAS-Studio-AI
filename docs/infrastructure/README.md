# Infrastructure DNS — Index

Production DNS documentation for **rtasstudio.com** (Vercel + Cloudflare).

Start here: **[DNS_EXECUTIVE_REPORT.md](./DNS_EXECUTIVE_REPORT.md)**  
Founder apply sheet: **[MANUAL_CLOUDFLARE_CHANGE_LIST.md](./MANUAL_CLOUDFLARE_CHANGE_LIST.md)**

| Document | Description |
|----------|-------------|
| [DNS_AUDIT_BEFORE.md](./DNS_AUDIT_BEFORE.md) | Pre-migration inventory of all live records |
| [DNS_DIFF_REPORT.md](./DNS_DIFF_REPORT.md) | Legacy vs official vs project-specific targets |
| [DNS_PRODUCTION_DEPLOYMENT.md](./DNS_PRODUCTION_DEPLOYMENT.md) | Deployment / optional migration guide |
| [DNS_COMPATIBILITY_REPORT.md](./DNS_COMPATIBILITY_REPORT.md) | Email, Paddle, TXT safety |
| [CLOUDFLARE_COMPATIBILITY.md](./CLOUDFLARE_COMPATIBILITY.md) | DNS-only, SSL, flattening, redirects |
| [DNS_ROLLBACK_PLAN.md](./DNS_ROLLBACK_PLAN.md) | Known-good rollback values |
| [PRODUCTION_DNS_CHECKLIST.md](./PRODUCTION_DNS_CHECKLIST.md) | End-to-end verification checklist |
| [EMAIL_SECURITY_AUDIT.md](./EMAIL_SECURITY_AUDIT.md) | SPF / DKIM / DMARC |
| [MANUAL_CLOUDFLARE_CHANGE_LIST.md](./MANUAL_CLOUDFLARE_CHANGE_LIST.md) | Exact Cloudflare add/edit/delete list |
| [DNS_EXECUTIVE_REPORT.md](./DNS_EXECUTIVE_REPORT.md) | CTO scorecard + verdict |

**Policy:** No automated production DNS mutations from agents. Manual Cloudflare changes only.
