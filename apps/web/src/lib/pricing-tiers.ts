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
  name: string;
  subtitle: string;
  price: number;
  priceSuffix: string;
  creditsLabel: string;
  highlights: string[];
  features: PricingFeatureRow[];
  featured?: boolean;
  ctaLabel: string;
};

export const PRICING_TIERS: PricingTier[] = [
  {
    plan: "tester",
    name: "Creator Starter",
    subtitle: "Pay-As-You-Go",
    price: TESTER_PRICE_USD,
    priceSuffix: "one-time",
    creditsLabel: `${TESTER_CREDITS}s · ${TESTER_DURATION_DAYS}-day access`,
    highlights: [
      "Full studio workflow — lyrics, identity & scenes",
      "End-to-end pipeline evaluation before subscription",
      "Ideal for first render and workflow validation",
    ],
    features: [
      { label: "Resolution", value: "720p HD evaluation", included: true },
      { label: "Watermark", value: "Evaluation watermark on exports", included: false },
      { label: "Identity-Lock queue", value: "Standard processing", included: true },
      { label: "Commercial download", value: "Preview license only", included: false },
    ],
    ctaLabel: `Start for $${TESTER_PRICE_USD}`,
  },
  {
    plan: "standard",
    name: "Pro Studio Tier",
    subtitle: "Monthly subscription",
    price: STANDARD_PRICE_USD,
    priceSuffix: "/month",
    creditsLabel: `${STANDARD_CREDITS}s monthly (≈33 min)`,
    featured: true,
    highlights: [
      "Clean HD exports for social, ads & brand content",
      "Commercial rights on all paid downloads",
      "Identity Shielding across multi-scene projects",
    ],
    features: [
      { label: "Resolution", value: "1080p HD master", included: true },
      { label: "Watermark", value: "Clean — no watermark", included: true },
      { label: "Identity-Lock queue", value: "Priority queuing", included: true },
      { label: "Commercial download", value: "Licensed commercial use", included: true },
    ],
    ctaLabel: `Go Pro — $${STANDARD_PRICE_USD}/mo`,
  },
  {
    plan: "premium",
    name: "Production Enterprise",
    subtitle: "Monthly subscription",
    price: PREMIUM_PRICE_USD,
    priceSuffix: "/month",
    creditsLabel: `${PREMIUM_CREDITS}s monthly (≈33 min)`,
    highlights: [
      "Cinematic 4K with film-grade colour science",
      "Advanced identity-lock for hero talent continuity",
      "Built for music videos, ads & premium brand films",
    ],
    features: [
      { label: "Resolution", value: "4K cinematic master", included: true },
      { label: "Watermark", value: "Clean — no watermark", included: true },
      { label: "Identity-Lock queue", value: "Priority+ enterprise queue", included: true },
      { label: "Commercial download", value: "Full enterprise license", included: true },
    ],
    ctaLabel: `Go Enterprise — $${PREMIUM_PRICE_USD}/mo`,
  },
];

export function planDisplayName(plan: PaidPlanType): string {
  const tier = PRICING_TIERS.find((t) => t.plan === plan);
  return tier?.name ?? plan;
}
