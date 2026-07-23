/** Phase 13 Sprint 9 — Global GTM launch types. No fabricated metrics. */

export type LaunchItemStatus =
  | "done"
  | "in_progress"
  | "planned"
  | "blocked"
  | "not_started";

export type LaunchOwner = "founder" | "engineering" | "marketing" | "sales" | "support" | "ops";

export type LaunchChecklistItem = {
  id: string;
  title: string;
  description: string;
  category:
    | "infra"
    | "security"
    | "marketing"
    | "sales"
    | "support"
    | "business"
    | "product";
  status: LaunchItemStatus;
  owner: LaunchOwner;
  milestoneId?: string;
  evidence?: string;
  /** When true, item is internal (founder/admin) only. */
  internal?: boolean;
};

export type LaunchMilestone = {
  id: string;
  title: string;
  targetLabel: string;
  status: LaunchItemStatus;
  summary: string;
};

export type CampaignChannel =
  | "youtube"
  | "linkedin"
  | "x"
  | "facebook"
  | "instagram"
  | "tiktok"
  | "reddit"
  | "product_hunt"
  | "google_ads"
  | "meta_ads";

export type CampaignPlan = {
  id: string;
  channel: CampaignChannel;
  name: string;
  objective: string;
  audience: string;
  contentPillars: string[];
  status: LaunchItemStatus;
  /** Structures only — never invent live metrics. */
  metricsNote: string;
  assetsNeeded: string[];
  owner: LaunchOwner;
  cta: string;
};

export type LaunchAssetKind =
  | "logo"
  | "screenshot"
  | "video"
  | "demo"
  | "media_kit"
  | "founder_bio"
  | "press_kit"
  | "brand_guidelines"
  | "other";

export type LaunchAsset = {
  id: string;
  title: string;
  kind: LaunchAssetKind;
  /** Public path or absolute URL when real; null when placeholder. */
  href: string | null;
  placeholder: boolean;
  notes: string;
};

export type RoadmapStatus = "completed" | "in_progress" | "planned" | "under_review";

export type RoadmapItem = {
  id: string;
  title: string;
  summary: string;
  status: RoadmapStatus;
  area: string;
};

export type ReadinessDimension =
  | "infra"
  | "security"
  | "marketing"
  | "sales"
  | "support"
  | "business";

export type ReadinessScore = {
  dimension: ReadinessDimension;
  score: number;
  max: number;
  label: string;
  notes: string;
};
