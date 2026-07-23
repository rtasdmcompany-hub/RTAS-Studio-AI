/** Shared affiliate/partner constants safe for client + server bundles. */

export const AFFILIATE_COMMISSION_PLACEHOLDER = {
  label: "Placeholder — not a live offer",
  standardFirstMonthPercent: "20–30%",
  premiumFirstMonthPercent: "10–15%",
  testerNote:
    "Tester-only conversions may earn $0 or a reduced rate to discourage $5 farming — final rates confirmed in writing before payouts enable.",
  base: "First paid conversion (Tester upgrade and/or first subscription month)",
} as const;

export const PARTNER_TYPES = [
  {
    id: "creative_agencies",
    title: "Creative & Marketing Agencies",
    body: "Agencies producing commercials, music videos, and brand films who want Studio capacity, licensing clarity, and co-marketing review.",
  },
  {
    id: "software",
    title: "Software",
    body: "Product and SaaS companies exploring integrations, embedded workflows, or joint GTM with RTAS Studio AI.",
  },
  {
    id: "education",
    title: "Education",
    body: "Schools, labs, and training programs evaluating Studio for coursework with authorized content only.",
  },
  {
    id: "technology",
    title: "Technology",
    body: "Platforms, tooling, and infrastructure partners extending Studio without inventing a public marketplace.",
  },
  {
    id: "enterprise",
    title: "Enterprise",
    body: "Larger organizations exploring Production Enterprise packaging, procurement, and Identity Preservation policy alignment.",
  },
] as const;

export type PartnerTypeId = (typeof PARTNER_TYPES)[number]["id"];

export const PARTNER_TYPE_IDS: PartnerTypeId[] = PARTNER_TYPES.map((t) => t.id);

export function isPartnerTypeId(value: string): value is PartnerTypeId {
  return (PARTNER_TYPE_IDS as string[]).includes(value);
}

export function buildReferralUrl(code: string, appOrigin?: string): string {
  const origin =
    appOrigin ||
    (typeof process !== "undefined"
      ? process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "")
      : undefined) ||
    "https://rtasstudio.com";
  return `${origin}/pricing?ref=${encodeURIComponent(code)}`;
}

export function generateReferralCode(seed: string): string {
  const cleaned = seed.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
  const base = (cleaned.slice(0, 6) || "RTAS").padEnd(4, "X");
  const suffix = Math.abs(
    Array.from(seed).reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
  )
    .toString(36)
    .toUpperCase()
    .slice(0, 4);
  return `RTAS-${base}${suffix}`.slice(0, 16);
}
