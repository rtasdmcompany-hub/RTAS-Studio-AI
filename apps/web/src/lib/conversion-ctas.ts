/**
 * Canonical conversion CTA labels for RTAS Studio AI.
 * Honest wording only — never imply free generation credits.
 * Entry product is paid Tester ($5 / 30s / 5 days). New accounts start at 0 credits.
 */

export const CTA = {
  /** Primary product entry — opens Studio (auth-gated). */
  START_CREATING: "Start creating",
  /** Explicit Tester purchase path. */
  GET_TESTER: "Get Tester",
  /** Open Studio for signed-in or returning users. */
  OPEN_STUDIO: "Open Studio",
  /** Plan comparison. */
  COMPARE_PLANS: "Compare plans",
  VIEW_PRICING: "View pricing",
  /** Enterprise. */
  ENTERPRISE_INQUIRY: "Enterprise inquiry",
  SCHEDULE_DEMO: "Schedule demo",
  /** Support / docs. */
  HELP_CENTER: "Help Center",
  CONTACT_SUPPORT: "Contact support",
  /** Learning. */
  HOW_TO_USE: "How to use",
  /** Billing. */
  UPGRADE_OPTIONS: "View upgrade options",
  CHANGE_PLAN: "Change plan",
} as const;

export type CtaLabel = (typeof CTA)[keyof typeof CTA];

/** Page → recommended primary / secondary CTA pair. */
export const PAGE_CTA_STRATEGY = {
  homepage: {
    primary: CTA.START_CREATING,
    primaryHref: "/studio",
    secondary: CTA.VIEW_PRICING,
    secondaryHref: "/pricing",
  },
  pricing: {
    primary: CTA.GET_TESTER,
    primaryHref: "/pricing#plans",
    secondary: CTA.COMPARE_PLANS,
    secondaryHref: "/pricing#plans",
  },
  features: {
    primary: CTA.VIEW_PRICING,
    primaryHref: "/pricing#plans",
    secondary: CTA.OPEN_STUDIO,
    secondaryHref: "/studio",
  },
  enterprise: {
    primary: CTA.SCHEDULE_DEMO,
    primaryHref: "/demo",
    secondary: CTA.ENTERPRISE_INQUIRY,
    secondaryHref: "/enterprise#contact",
  },
  blog: {
    primary: CTA.START_CREATING,
    primaryHref: "/studio",
    secondary: CTA.VIEW_PRICING,
    secondaryHref: "/pricing",
  },
  docs: {
    primary: CTA.OPEN_STUDIO,
    primaryHref: "/studio",
    secondary: CTA.HOW_TO_USE,
    secondaryHref: "/how-to-use",
  },
  support: {
    primary: CTA.HELP_CENTER,
    primaryHref: "/help",
    secondary: CTA.CONTACT_SUPPORT,
    secondaryHref: "/help/contact",
  },
} as const;
