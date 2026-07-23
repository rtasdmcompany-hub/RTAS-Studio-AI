/**
 * Central commercial link config for RTAS Studio AI.
 * Update URLs here — footer, trust, and marketing chrome read from this file.
 */

export type SiteNavLink = {
  id: string;
  label: string;
  href: string;
  external?: boolean;
};

export type SiteSocialLink = {
  id: string;
  label: string;
  href: string;
  /** Short glyph used when SVG icons are unavailable */
  glyph: string;
};

/** Product column */
export const SITE_PRODUCT_LINKS: SiteNavLink[] = [
  { id: "studio", label: "Studio", href: "/studio" },
  { id: "dashboard", label: "Dashboard", href: "/profile" },
  { id: "showcase", label: "Showcase", href: "/showcase" },
  { id: "features", label: "Features", href: "/features" },
  { id: "pricing", label: "Pricing", href: "/pricing" },
  { id: "enterprise", label: "Enterprise", href: "/enterprise" },
  { id: "demo", label: "Schedule Demo", href: "/demo" },
  { id: "beta", label: "Public Beta", href: "/beta" },
];

/** Company column */
export const SITE_COMPANY_LINKS: SiteNavLink[] = [
  { id: "about", label: "About", href: "/about" },
  { id: "careers", label: "Careers", href: "/careers" },
  { id: "partners", label: "Partners", href: "/partners" },
  { id: "blog", label: "Blog", href: "/blog" },
  { id: "contact", label: "Contact", href: "/help/contact" },
  { id: "community", label: "Community", href: "https://discord.gg/rtas", external: true },
];

/** Developers column */
export const SITE_DEVELOPER_LINKS: SiteNavLink[] = [
  { id: "developers", label: "Developers", href: "/developers" },
  { id: "api-docs", label: "API documentation", href: "/docs" },
  { id: "status", label: "Status", href: "/status" },
  {
    id: "github",
    label: "GitHub",
    href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI",
    external: true,
  },
];

/** Resources column */
export const SITE_RESOURCE_LINKS: SiteNavLink[] = [
  { id: "docs", label: "Documentation", href: "/docs" },
  { id: "how", label: "How to use", href: "/how-to-use" },
  { id: "help", label: "Customer Success", href: "/help" },
  { id: "faq", label: "FAQ", href: "/help/faq" },
  { id: "billing", label: "Billing", href: "/help/billing" },
  { id: "changelog", label: "Release Notes", href: "/help/changelog" },
];

/**
 * Paddle Merchant of Record required policies — exact labels Paddle expects
 * ("Terms of Service", "Privacy Policy" / privacy notice, "Refund Policy").
 * Shown first in the Legal column and again in the footer bottom strip.
 */
export const SITE_PADDLE_POLICY_LINKS: SiteNavLink[] = [
  { id: "terms", label: "Terms of Service", href: "/terms" },
  { id: "privacy", label: "Privacy Policy", href: "/privacy" },
  { id: "refund", label: "Refund Policy", href: "/refund" },
];

/** Legal column */
export const SITE_LEGAL_LINKS: SiteNavLink[] = [
  ...SITE_PADDLE_POLICY_LINKS,
  { id: "trust-safety", label: "Trust & Safety", href: "/trust-safety" },
  { id: "ai-policy", label: "AI Usage Policy", href: "/ai-policy" },
  { id: "cookies", label: "Cookie Policy", href: "/cookies" },
];

/** Support aliases (help surfaces) */
export const SITE_SUPPORT_LINKS: SiteNavLink[] = [
  { id: "help", label: "Help Center", href: "/help" },
  { id: "contact-support", label: "Contact", href: "/help/contact" },
  ...SITE_PADDLE_POLICY_LINKS,
  { id: "trust-safety", label: "Trust & Safety", href: "/trust-safety" },
  { id: "ai-policy", label: "AI Usage Policy", href: "/ai-policy" },
  { id: "cookies", label: "Cookie Policy", href: "/cookies" },
  { id: "status", label: "System status", href: "/status" },
  { id: "faq", label: "FAQ", href: "/help/faq" },
  { id: "billing", label: "Billing", href: "/help/billing" },
];

export const SITE_SOCIAL_LINKS: SiteSocialLink[] = [
  {
    id: "youtube",
    label: "YouTube",
    href: "https://www.youtube.com/@RTASDigital",
    glyph: "▶",
  },
  {
    id: "facebook",
    label: "Facebook",
    href: "https://www.facebook.com/RTASDigital",
    glyph: "f",
  },
  {
    id: "instagram",
    label: "Instagram",
    href: "https://www.instagram.com/rtasdigital",
    glyph: "◎",
  },
  {
    id: "tiktok",
    label: "TikTok",
    href: "https://www.tiktok.com/@rtasdigital",
    glyph: "♪",
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    href: "https://www.linkedin.com/company/rtas-digital",
    glyph: "in",
  },
  {
    id: "x",
    label: "X",
    href: "https://x.com/RTASDigital",
    glyph: "𝕏",
  },
  {
    id: "github",
    label: "GitHub",
    href: "https://github.com/rtasdmcompany-hub/RTAS-Studio-AI",
    glyph: "⌘",
  },
  {
    id: "discord",
    label: "Discord",
    href: "https://discord.gg/rtas",
    glyph: "◈",
  },
];

/** Primary public contact (footer, contact page, careers, feedback). */
export const SITE_SUPPORT_EMAIL = "contact@rtasstudio.com";
/** Support / help desk alias — use in help FAQ and support-specific CTAs. */
export const SITE_HELP_EMAIL = "support@rtasstudio.com";
/** General info alias. */
export const SITE_INFO_EMAIL = "info@rtasstudio.com";
/** Designated legal correspondence address (Forward Email / routing). */
export const SITE_LEGAL_EMAIL = "legal@rtasstudio.com";
/** Designated privacy / data-rights address (Forward Email / routing). */
export const SITE_PRIVACY_EMAIL = "privacy@rtasstudio.com";

export const SITE_TRUST_BADGES = [
  {
    id: "enterprise",
    label: "Built for Teams",
    description: "Studio workflows for creators, agencies, and marketing orgs",
  },
  {
    id: "secure-ai",
    label: "Secure AI Processing",
    description: "Cloud pipeline with guarded API access",
  },
  {
    id: "privacy",
    label: "Privacy First",
    description: "Your assets stay under your control",
  },
  {
    id: "encrypted",
    label: "Encrypted",
    description: "TLS in transit · secrets never in the client",
  },
  {
    id: "license",
    label: "Commercial License",
    description: "Paid tiers unlock licensed downloads",
  },
  {
    id: "cloud",
    label: "Fast Cloud Processing",
    description: "GPU workers with live progress feedback",
  },
  {
    id: "uptime",
    label: "Monitored Hosting",
    description: "Health endpoints and operational monitoring",
  },
] as const;
