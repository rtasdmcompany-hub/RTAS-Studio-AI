/**
 * Help Center knowledge base — searchable articles by category.
 * Content only; no fabricated ticket volumes or SLAs.
 */

export const HELP_CATEGORIES = [
  { id: "account", label: "Account", description: "Sign-in, verification, profile, and access." },
  { id: "billing", label: "Billing", description: "Plans, renewals, invoices, and Paddle MoR." },
  { id: "credits", label: "Credits", description: "Credit math, pools, expiry, and usage." },
  { id: "video_generation", label: "Video Generation", description: "Compose, render, stitch, and downloads." },
  { id: "templates", label: "Templates", description: "Category templates and starting points." },
  { id: "ai_models", label: "AI Models", description: "Providers, quality tiers, and 4K." },
  { id: "enterprise", label: "Enterprise", description: "Teams, demos, proposals, and Identity Preservation." },
  { id: "api", label: "API", description: "Developer docs and integration paths." },
  { id: "security", label: "Security", description: "Auth, authorized use, and trust policies." },
  { id: "technical", label: "Technical Issues", description: "Errors, browsers, and troubleshooting." },
] as const;

export type HelpCategoryId = (typeof HELP_CATEGORIES)[number]["id"];

export type HelpArticle = {
  id: string;
  category: HelpCategoryId;
  title: string;
  body: string;
  href?: string;
  tags: string[];
};

export const HELP_ARTICLES: HelpArticle[] = [
  {
    id: "account-start",
    category: "account",
    title: "Where do I start after signing up?",
    body: "Open your Dashboard to see credits, then launch Studio. A short welcome guide appears on first visit. Verify your email if prompted — Studio requires a verified account.",
    href: "/how-to-use",
    tags: ["onboarding", "dashboard", "studio"],
  },
  {
    id: "account-verify",
    category: "account",
    title: "How do I verify my email?",
    body: "Check your inbox for the RTAS verification link. If it expired, use Check email / resend from the auth flow. Unverified accounts cannot open Studio or Dashboard.",
    href: "/auth/check-email",
    tags: ["email", "verification", "login"],
  },
  {
    id: "account-login",
    category: "account",
    title: "I cannot sign in",
    body: "Confirm you are using the same method you registered with (email/password vs Google). Password accounts cannot be silently taken over by Google. Use Forgot password if needed.",
    href: "/auth/forgot-password",
    tags: ["login", "password", "google"],
  },
  {
    id: "billing-plans",
    category: "billing",
    title: "What plans are available?",
    body: "Tester $5 · 30 seconds · 5 days. Standard $89/mo · 2000 seconds. Premium 4K $249/mo · 2000 seconds. Checkout is processed by Paddle as Merchant of Record when live.",
    href: "/pricing",
    tags: ["pricing", "tester", "standard", "premium"],
  },
  {
    id: "billing-renewal",
    category: "billing",
    title: "How do renewals and invoices work?",
    body: "Paid subscriptions renew on the billing cycle shown in Dashboard. Invoices and purchase history appear under Billing when your payment provider has recorded them — we never invent invoice rows.",
    href: "/help/billing",
    tags: ["renewal", "invoice", "paddle"],
  },
  {
    id: "billing-refund",
    category: "billing",
    title: "Where is the refund policy?",
    body: "See the Refund Policy page. Refunds for MoR purchases follow Paddle’s process plus our published policy.",
    href: "/refund",
    tags: ["refund", "policy"],
  },
  {
    id: "credits-math",
    category: "credits",
    title: "What is a credit?",
    body: "1 credit equals 1 second of finished video. Your plan grants a credit pool that expires at the end of the billing period (Tester: 5 days).",
    href: "/help/billing",
    tags: ["credits", "seconds"],
  },
  {
    id: "credits-low",
    category: "credits",
    title: "What if I run out of credits?",
    body: "Generation is blocked when balance is insufficient — Studio shows a paywall. Upgrade or wait for the next pool if on a monthly plan. Unused seconds do not carry over after expiry.",
    href: "/pricing",
    tags: ["paywall", "upgrade", "balance"],
  },
  {
    id: "video-preview",
    category: "video_generation",
    title: "Why can’t I download a preview?",
    body: "Free previews are for review only. Paid plans unlock downloadable masters and commercial license entitlement on active subscriptions.",
    href: "/help/faq",
    tags: ["download", "preview", "commercial"],
  },
  {
    id: "video-render-time",
    category: "video_generation",
    title: "How long does a render take?",
    body: "Most short clips finish in a few minutes. Longer videos are split into segments and stitched automatically. You receive an email when the job is ready.",
    href: "/help/troubleshooting",
    tags: ["render", "eta", "stitch"],
  },
  {
    id: "video-failed",
    category: "video_generation",
    title: "My generation failed",
    body: "Open Troubleshooting for common causes (prompt/media, provider outage, credit debit). Retry from Studio or open a support ticket with the job ID from Dashboard.",
    href: "/help/troubleshooting",
    tags: ["failed", "error", "job"],
  },
  {
    id: "templates-categories",
    category: "templates",
    title: "How do category templates work?",
    body: "Use How to use and the landing showcase categories for starting points. Templates guide compose settings — they do not invent finished customer videos.",
    href: "/how-to-use",
    tags: ["templates", "categories", "showcase"],
  },
  {
    id: "models-tiers",
    category: "ai_models",
    title: "What is the difference between Standard and Premium 4K?",
    body: "Standard targets HD commercial output. Premium 4K unlocks the cinematic 4K path at $249/mo with the same 2000-second monthly pool. Model routing follows your active tier.",
    href: "/pricing",
    tags: ["4k", "hd", "models"],
  },
  {
    id: "enterprise-identity",
    category: "enterprise",
    title: "What is Authorized Identity Preservation?",
    body: "Identity-consistent generation is for authorized use only — not unauthorized face-swap or deepfake. Enterprise buyers should discuss authorized workflows on the Enterprise page.",
    href: "/enterprise",
    tags: ["identity", "authorized", "enterprise"],
  },
  {
    id: "enterprise-demo",
    category: "enterprise",
    title: "How do I book an enterprise demo?",
    body: "Use Schedule Demo or the Enterprise form. Leads are stored only when submitted — we do not seed fake pipeline deals.",
    href: "/demo",
    tags: ["demo", "sales", "teams"],
  },
  {
    id: "api-docs",
    category: "api",
    title: "Where are API docs?",
    body: "Start at /docs and the Developers page. Public API surface expands over time — do not assume undocumented endpoints.",
    href: "/docs",
    tags: ["api", "developers", "docs"],
  },
  {
    id: "security-trust",
    category: "security",
    title: "Where are trust and AI policies?",
    body: "See Trust & Safety, AI Usage Policy, Privacy, and Terms. Report abuse via support email or a Security-category ticket.",
    href: "/trust-safety",
    tags: ["trust", "privacy", "ai policy"],
  },
  {
    id: "technical-browser",
    category: "technical",
    title: "Studio looks broken in my browser",
    body: "Use a current Chromium-based browser or Safari. Disable aggressive content blockers on rtasstudio.com. Clear cache if assets fail to load after a deploy.",
    href: "/help/troubleshooting",
    tags: ["browser", "cache", "ui"],
  },
  {
    id: "technical-status",
    category: "technical",
    title: "Is the platform down?",
    body: "Check System Status for live health probes. If generation providers are degraded, jobs may fail until recovery — credits handling follows product rules, not invented SLAs.",
    href: "/status",
    tags: ["status", "outage", "health"],
  },
];

export function searchHelpArticles(query: string, category?: HelpCategoryId | "all"): HelpArticle[] {
  const q = query.trim().toLowerCase();
  return HELP_ARTICLES.filter((article) => {
    if (category && category !== "all" && article.category !== category) return false;
    if (!q) return true;
    const hay = [
      article.title,
      article.body,
      article.category,
      ...article.tags,
    ]
      .join(" ")
      .toLowerCase();
    return hay.includes(q) || q.split(/\s+/).every((token) => hay.includes(token));
  });
}

export function articlesByCategory(category: HelpCategoryId): HelpArticle[] {
  return HELP_ARTICLES.filter((a) => a.category === category);
}
