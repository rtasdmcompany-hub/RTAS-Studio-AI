import type { IdentityPipelineConfig } from "./identity-pipeline";

export type GenerationMode = "prompt" | "image";

export type VisualStyle = "real" | "avatar" | "cartoon";

export type VideoCategory =
  | "song"
  | "islamic"
  | "business"
  | "cartoon"
  | "story"
  | "podcast";

export type FieldType = "text" | "textarea" | "file" | "select" | "number";

export interface CategoryField {
  id: string;
  label: string;
  shortLabel: string;
  type: FieldType;
  placeholder?: string;
  options?: { value: string; label: string }[];
  required?: boolean;
  accept?: string;
  helpText?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  tier: "free" | "tester" | "standard" | "premium";
  freeTrialUsed: boolean;
  /** Server-side anti-abuse flag (mirrors freeTrialUsed) */
  hasUsedFreeTrial: boolean;
  credits: number;
  creditsExpireAt: string | null;
  subscriptionActive: boolean;
  subscriptionRenewsAt: string | null;
  previewSkipsRemaining: number;
  ipAddress?: string | null;
  deviceFingerprint?: string | null;
  paymentProvider?: import("./payments").PaymentProvider;
  externalCustomerId?: string;
  externalSubscriptionId?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface GeneratedVideo {
  id: string;
  userId: string;
  title: string;
  category: VideoCategory;
  mode: GenerationMode;
  visualStyle: VisualStyle;
  durationSeconds: number;
  creditsUsed: number;
  previewOnly: boolean;
  canDownload: boolean;
  status: "queued" | "processing" | "ready" | "failed";
  videoUrl?: string;
  thumbnailUrl?: string;
  /** True when backend used simulation / preview sample instead of live render. */
  simulationMode?: boolean;
  createdAt: string;
}

export interface GenerationRequest {
  mode: GenerationMode;
  category: VideoCategory;
  visualStyle: VisualStyle;
  durationSeconds: number;
  fields: Record<string, string>;
  skipSubscriptionCheck?: boolean;
  identityPipeline?: IdentityPipelineConfig;
  files?: Record<string, { name: string; mimeType: string; size: number }>;
}
