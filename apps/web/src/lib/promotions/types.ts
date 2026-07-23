export const PROMOTION_TYPES = [
  "internal",
  "partner",
  "educational",
] as const;

export const PROMOTION_STATUSES = [
  "draft",
  "active",
  "paused",
  "archived",
] as const;

export const PROMOTION_ACTIONS = [
  "view",
  "click",
  "dismiss",
  "conversion",
] as const;

export const PROMOTION_PLACEMENTS = [
  "homepage_announcement",
  "dashboard_sidebar",
  "studio_recommendations",
  "billing_upgrade",
  "credits_upgrade",
  "enterprise_cta",
  "docs_partner_recommendations",
  "learning_center",
  "blog_affiliate_recommendations",
] as const;

export type PromotionType = (typeof PROMOTION_TYPES)[number];
export type PromotionStatus = (typeof PROMOTION_STATUSES)[number];
export type PromotionAction = (typeof PROMOTION_ACTIONS)[number];
export type PromotionPlacement = (typeof PROMOTION_PLACEMENTS)[number];

export type PromotionAudienceRules = {
  audiences?: Array<"free_user" | "paid_user" | "enterprise_lead">;
  countries?: string[];
  languages?: string[];
  plans?: string[];
  minCredits?: number;
  maxCredits?: number;
  recentActivity?: Array<
    "active_last_7d" | "inactive_14d" | "generated_last_30d" | "no_generation_30d"
  >;
};

export type PromotionVariant = {
  id: string;
  headline?: string;
  body?: string;
  ctaLabel?: string;
  imageUrl?: string;
  placement?: string;
  audienceOverrides?: PromotionAudienceRules;
};

export type PromotionRecord = {
  id: string;
  slug: string;
  title: string;
  description: string;
  promotionType: PromotionType;
  sponsorName: string | null;
  sponsorLabel: string | null;
  status: PromotionStatus;
  targetPage: string;
  placements: string[];
  audienceRules: PromotionAudienceRules | null;
  variants: PromotionVariant[];
  ctaLabel: string;
  ctaHref: string;
  ctaKind: "link" | "checkout";
  checkoutPlan: "tester" | "standard" | "premium" | null;
  imageUrl: string | null;
  badgeText: string | null;
  priority: number;
  dismissible: boolean;
  revenueValueCents: number;
  startAt: string | null;
  endAt: string | null;
  metadataJson: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
};

export type PromotionResolved = {
  promotion: PromotionRecord;
  variant: PromotionVariant | null;
  placement: string;
  pagePath: string;
};

export type PromotionViewerContext = {
  userId?: string;
  sessionId: string;
  audience: "free_user" | "paid_user" | "enterprise_lead";
  plan: string;
  credits: number;
  country: string;
  language: string;
  recentActivity: {
    activeLast7d: boolean;
    inactive14d: boolean;
    generatedLast30d: boolean;
    noGeneration30d: boolean;
  };
};

export type PromotionMetrics = {
  views: number;
  clicks: number;
  ctr: number;
  dismisses: number;
  dismissRate: number;
  conversions: number;
  revenueGeneratedUsd: number;
};

export type PromotionAdminRow = PromotionRecord & {
  metrics: PromotionMetrics;
};
