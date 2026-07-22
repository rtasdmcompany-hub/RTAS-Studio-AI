import type { PaidPlanType } from "@rtas/shared";
import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";

export type PricingFeatureRow = {
  label: string;
  value: string;
  included: boolean;
};

export type PricingTier = {
  plan: PaidPlanType;
  /** Canonical product name (checkout / billing source of truth). */
  name: string;
  /** Optional marketing alias shown under the canonical name. */
  marketingAlias?: string;
  subtitle: string;
  price: number;
  priceSuffix: string;
  creditsLabel: string;
  bestFor: string;
  highlights: string[];
  features: PricingFeatureRow[];
  featured?: boolean;
  ctaLabel: string;
};

/**
 * Public plan cards.
 * Canonical names: Tester · Standard · Premium 4K
 * Marketing aliases (optional display): Creator Starter · Pro Studio · Production Enterprise
 */
export const PRICING_TIERS: PricingTier[] = [
  {
    plan: "tester",
    name: "Tester",
    marketingAlias: "Creator Starter",
    subtitle: "One-time evaluation",
    price: TESTER_PRICE_USD,
    priceSuffix: "one-time",
    creditsLabel: `${TESTER_CREDITS}s · ${TESTER_DURATION_DAYS}-day access`,
    bestFor: "First real render before you subscribe",
    highlights: [
      "Full studio workflow — lyrics, identity & scenes",
      "Validate the pipeline end-to-end",
      "No monthly commitment",
    ],
    features: [
      { label: "Resolution", value: "720p HD evaluation", included: true },
      { label: "Watermark", value: "Evaluation watermark on exports", included: false },
      { label: "Identity Preservation queue", value: "Standard processing", included: true },
      { label: "Commercial download", value: "Preview license only", included: false },
    ],
    ctaLabel: `Start Tester — $${TESTER_PRICE_USD}`,
  },
  {
    plan: "standard",
    name: "Standard",
    marketingAlias: "Pro Studio",
    subtitle: "Most popular · Monthly",
    price: STANDARD_PRICE_USD,
    priceSuffix: "/month",
    creditsLabel: `${STANDARD_CREDITS}s monthly (~33 min)`,
    bestFor: "Creators shipping social, ads & brand clips",
    featured: true,
    highlights: [
      "Clean 1080p masters — no watermark",
      "Commercial rights on paid downloads",
      "Priority Identity Preservation queuing",
    ],
    features: [
      { label: "Resolution", value: "1080p HD master", included: true },
      { label: "Watermark", value: "Clean — no watermark", included: true },
      { label: "Identity Preservation queue", value: "Priority queuing", included: true },
      { label: "Commercial download", value: "Licensed commercial use", included: true },
    ],
    ctaLabel: `Go Standard — $${STANDARD_PRICE_USD}/mo`,
  },
  {
    plan: "premium",
    name: "Premium 4K",
    marketingAlias: "Production Enterprise",
    subtitle: "Cinematic · Monthly",
    price: PREMIUM_PRICE_USD,
    priceSuffix: "/month",
    creditsLabel: `${PREMIUM_CREDITS}s monthly (~33 min)`,
    bestFor: "Music videos, ads & premium brand films in 4K",
    highlights: [
      "Cinematic 4K with film-grade colour",
      "Advanced identity continuity for hero talent",
      "Priority+ queue for production deadlines",
    ],
    features: [
      { label: "Resolution", value: "4K cinematic master", included: true },
      { label: "Watermark", value: "Clean — no watermark", included: true },
      { label: "Identity Preservation queue", value: "Priority+ enterprise queue", included: true },
      { label: "Commercial download", value: "Full commercial license", included: true },
    ],
    ctaLabel: `Go Premium 4K — $${PREMIUM_PRICE_USD}/mo`,
  },
];

export function planDisplayName(plan: PaidPlanType): string {
  const tier = PRICING_TIERS.find((t) => t.plan === plan);
  return tier?.name ?? plan;
}
