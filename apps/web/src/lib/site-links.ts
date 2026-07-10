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
  { id: "pricing", label: "Pricing", href: "/pricing" },
  { id: "features", label: "Features", href: "/#features" },
  { id: "docs", label: "Documentation", href: "/how-to-use" },
  { id: "developers", label: "Developers", href: "/help" },
  { id: "dashboard", label: "Dashboard", href: "/profile" },
];

/** Company column */
export const SITE_COMPANY_LINKS: SiteNavLink[] = [
  { id: "about", label: "About", href: "/about" },
  { id: "careers", label: "Careers", href: "/support" },
  { id: "blog", label: "Blog", href: "/help/changelog" },
  { id: "contact", label: "Contact", href: "/support" },
];

/** Support column */
export const SITE_SUPPORT_LINKS: SiteNavLink[] = [
  { id: "help", label: "Help Center", href: "/help" },
  { id: "contact-support", label: "Contact", href: "/support" },
  { id: "privacy", label: "Privacy", href: "/privacy" },
  { id: "terms", label: "Terms", href: "/terms" },
  { id: "cookies", label: "Cookie Policy", href: "/cookies" },
  { id: "status", label: "Status", href: "/api/health" },
  { id: "faq", label: "FAQ", href: "/help/faq" },
  { id: "billing", label: "Billing", href: "/help/billing" },
];

/** Legal (subset used where a dedicated Legal column is shown) */
export const SITE_LEGAL_LINKS: SiteNavLink[] = [
  { id: "privacy", label: "Privacy", href: "/privacy" },
  { id: "terms", label: "Terms", href: "/terms" },
  { id: "cookies", label: "Cookie Policy", href: "/cookies" },
];

/**
 * Social profiles — replace placeholder URLs when official accounts go live.
 * Keep ids stable; UI maps icons by id.
 */
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

export const SITE_SUPPORT_EMAIL = "support@rtasdigital.com";

/** Tasteful trust copy — never exaggerate beyond product reality */
export const SITE_TRUST_BADGES = [
  {
    id: "enterprise",
    label: "Enterprise Ready",
    description: "Built for teams that ship at scale",
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
    label: "99.9% Availability",
    description: "Monitored hosting with health endpoints",
  },
] as const;
