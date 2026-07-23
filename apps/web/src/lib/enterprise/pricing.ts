/**
 * Phase 13 Sprint 2 — Enterprise commercial naming vs published SKUs.
 * Public pricing truth lives in @rtas/shared; Enterprise has no fixed price.
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

export type EnterpriseCommercialTier = "tester" | "creator" | "business" | "enterprise";

export type EnterpriseTierAvailability = "self_serve" | "contact_sales";

export type EnterpriseCommercialTierCard = {
  id: EnterpriseCommercialTier;
  /** GTM / enterprise sales name */
  name: string;
  /** Maps to published product plan — honest alias */
  mapsTo: string;
  priceLabel: string;
  priceDetail: string;
  creditsLabel: string;
  cta: { label: string; href: string };
  availability: EnterpriseTierAvailability;
  highlights: string[];
  /** Never invent enterprise list price */
  fixedPrice: boolean;
};

export const ENTERPRISE_COMMERCIAL_TIERS: EnterpriseCommercialTierCard[] = [
  {
    id: "tester",
    name: "Tester",
    mapsTo: "Tester (published)",
    priceLabel: `$${TESTER_PRICE_USD}`,
    priceDetail: `${TESTER_DURATION_DAYS}-day evaluation`,
    creditsLabel: `${TESTER_CREDITS} seconds`,
    cta: { label: "Start Tester", href: "/pricing" },
    availability: "self_serve",
    highlights: [
      "Self-serve evaluation",
      "1 credit = 1 second",
      "No long-term commitment",
    ],
    fixedPrice: true,
  },
  {
    id: "creator",
    name: "Creator",
    mapsTo: `Standard — $${STANDARD_PRICE_USD}/mo`,
    priceLabel: `$${STANDARD_PRICE_USD}/mo`,
    priceDetail: "Published as Standard on /pricing",
    creditsLabel: `${STANDARD_CREDITS} seconds / month`,
    cta: { label: "Choose Standard", href: "/pricing" },
    availability: "self_serve",
    highlights: [
      "Commercial downloads on paid tier",
      "Studio compose → render → export",
      "Transparent credit metering",
    ],
    fixedPrice: true,
  },
  {
    id: "business",
    name: "Business",
    mapsTo: `Premium 4K — $${PREMIUM_PRICE_USD}/mo`,
    priceLabel: `$${PREMIUM_PRICE_USD}/mo`,
    priceDetail: "Published as Premium 4K / Production Enterprise",
    creditsLabel: `${PREMIUM_CREDITS} seconds / month · cinematic 4K capacity`,
    cta: { label: "Choose Premium", href: "/pricing" },
    availability: "self_serve",
    highlights: [
      "Cinematic 4K capacity",
      "Brand & music production workflows",
      "Same credit economics (1 credit = 1 second)",
    ],
    fixedPrice: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    mapsTo: "Custom commercial terms (no public SKU price)",
    priceLabel: "Contact Sales",
    priceDetail: "Proposal-based · no fixed public price",
    creditsLabel: "Scoped volume, seats, and services",
    cta: { label: "Request Proposal", href: "/enterprise#contact" },
    availability: "contact_sales",
    highlights: [
      "Custom onboarding & account support",
      "Security / deployment scoping",
      "Volume & procurement terms via proposal",
    ],
    fixedPrice: false,
  },
];
