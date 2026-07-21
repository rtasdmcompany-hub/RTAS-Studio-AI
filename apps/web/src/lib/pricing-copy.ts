/**
 * Pricing conversion copy — commercial voice, honest economics.
 * Prices and credit pools always come from @rtas/shared.
 */

import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";

export const PRICING_HERO_EYEBROW = "Transparent global pricing";

export const PRICING_HERO_HEADLINE = "Pick the plan that matches your next render.";

export const PRICING_HERO_SUPPORT =
  "1 credit = 1 second of finished video. Start with a one-time evaluation, then scale to monthly HD or cinematic 4K — merchant-of-record checkout worldwide.";

export const PRICING_VALUE_POINTS = [
  {
    id: "credit",
    title: "1 credit = 1 second",
    body: "No opaque tokens. Duration you render is what you spend.",
  },
  {
    id: "checkout",
    title: "Global checkout",
    body: "Merchant of Record handles tax and cards. RTAS never stores card data.",
  },
  {
    id: "license",
    title: "Commercial when paid",
    body: "Active Pro and Enterprise unlock clean masters and commercial entitlement.",
  },
] as const;

export const PRICING_AUDIENCE_GUIDE = [
  {
    id: "tester",
    planHint: "Creator Starter",
    title: "Evaluating the pipeline",
    body: `One real clip end-to-end for $${TESTER_PRICE_USD}. ${TESTER_CREDITS}s · ${TESTER_DURATION_DAYS}-day access. Watermarked evaluation exports.`,
  },
  {
    id: "standard",
    planHint: "Pro Studio",
    title: "Shipping weekly content",
    body: `$${STANDARD_PRICE_USD}/mo · ${STANDARD_CREDITS}s (~33 min). Clean 1080p, commercial downloads, priority Identity Preservation queue.`,
  },
  {
    id: "premium",
    planHint: "Production Enterprise",
    title: "4K brand & music films",
    body: `$${PREMIUM_PRICE_USD}/mo · ${PREMIUM_CREDITS}s at cinematic 4K. Priority+ queue for ads, music videos, and hero talent continuity.`,
  },
] as const;

export type PricingFaqItem = {
  id: string;
  question: string;
  answer: string;
};

export const PRICING_FAQ: PricingFaqItem[] = [
  {
    id: "credits",
    question: "How do credits work?",
    answer:
      "1 credit equals 1 second of rendered video. Monthly pools reset each billing period. Early resubscribe may roll unused credits forward when offered in-app.",
  },
  {
    id: "starter",
    question: "Is Creator Starter a subscription?",
    answer: `No. It is a $${TESTER_PRICE_USD} one-time evaluation with ${TESTER_CREDITS}s and a ${TESTER_DURATION_DAYS}-day access window. Exports carry an evaluation watermark and preview license only.`,
  },
  {
    id: "pro-vs-enterprise",
    question: "Pro vs Enterprise — what changes?",
    answer:
      "Both include the same monthly credit pool. Pro delivers clean 1080p HD masters. Enterprise unlocks cinematic 4K, advanced identity continuity, and priority+ queuing.",
  },
  {
    id: "cancel",
    question: "Can I cancel anytime?",
    answer:
      "Yes. Manage or cancel from Dashboard → Manage plans. You keep access through the paid period; unused monthly credits expire at period end unless rollover applies.",
  },
  {
    id: "payment",
    question: "Who processes payment?",
    answer:
      "Checkout runs through our Merchant of Record, Paddle. Local currency may appear at checkout. Card data never touches RTAS servers.",
  },
  {
    id: "commercial",
    question: "When do I get commercial rights?",
    answer:
      "Active Pro and Enterprise plans unlock downloadable masters and commercial entitlement. Evaluation and free previews are for review only.",
  },
];

export const PRICING_FINAL_CTA_TITLE = "Ready when your next video is.";

export const PRICING_FINAL_CTA_BODY =
  "Choose a plan above, or open Studio and upgrade when you need credits.";
