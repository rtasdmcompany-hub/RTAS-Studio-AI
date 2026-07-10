# Product FAQ

**Q: Is this Stripe?**  
A: No. Merchant of Record is **Paddle** (default) or **Lemon Squeezy**.

**Q: Is auth Supabase Auth?**  
A: No. **NextAuth** (email/password + Google) with Prisma/Postgres.

**Q: What is a credit?**  
A: 1 credit = 1 second of finished video.

**Q: Where do I go after signup?**  
A: Dashboard (`/profile`) with a short welcome, then Studio.

**Q: Can I use the product without a custom domain?**  
A: Yes on `rtas-studio-ai-web.vercel.app`. Production domain is added later without code changes.

**Q: Why is `/api/ready` 503?**  
A: Missing production credentials (e.g. `FASTAPI_URL`, Paddle webhook). App still serves; commercial readiness waits on env.

More: `/help` in the app.
