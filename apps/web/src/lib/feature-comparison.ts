/**
 * Feature comparison — plan matrix + workflow contrast.
 * Keep claims honest; never invent competitor product names or fake scores.
 */

export type PlanCell = "yes" | "no" | "partial" | string;

export type FeatureMatrixRow = {
  id: string;
  category: string;
  feature: string;
  starter: PlanCell;
  pro: PlanCell;
  enterprise: PlanCell;
};

export const FEATURE_CAPABILITIES = [
  {
    id: "compose",
    title: "Compose",
    body: "Lyrics, audio, scenes, and identity references in one guided workspace.",
  },
  {
    id: "identity",
    title: "Identity lock",
    body: "Real-face mode keeps likeness consistent across multi-scene projects.",
  },
  {
    id: "render",
    title: "Cloud render",
    body: "GPU pipeline with live progress — from evaluation HD to cinematic 4K.",
  },
  {
    id: "publish",
    title: "Library & share",
    body: "Store masters, share publicly, and download when your plan unlocks commercial rights.",
  },
] as const;

export const FEATURE_MATRIX: FeatureMatrixRow[] = [
  {
    id: "studio-workflow",
    category: "Studio",
    feature: "Full compose → render → publish workflow",
    starter: "yes",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "lyrics-audio",
    category: "Studio",
    feature: "Lyrics + audio sync tools",
    starter: "yes",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "identity-lock",
    category: "Studio",
    feature: "Identity-lock / real-face continuity",
    starter: "Standard queue",
    pro: "Priority queue",
    enterprise: "Priority+",
  },
  {
    id: "resolution",
    category: "Output",
    feature: "Max export resolution",
    starter: "720p",
    pro: "1080p HD",
    enterprise: "4K cinematic",
  },
  {
    id: "watermark",
    category: "Output",
    feature: "Clean (no watermark) masters",
    starter: "no",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "commercial",
    category: "Output",
    feature: "Commercial download license",
    starter: "Preview only",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "credits",
    category: "Credits",
    feature: "Credit model",
    starter: "30s one-time",
    pro: "2000s / mo",
    enterprise: "2000s / mo",
  },
  {
    id: "credit-math",
    category: "Credits",
    feature: "1 credit = 1 second",
    starter: "yes",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "library",
    category: "Workspace",
    feature: "Project library & share links",
    starter: "yes",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "dashboard",
    category: "Workspace",
    feature: "Dashboard credits & plan management",
    starter: "yes",
    pro: "yes",
    enterprise: "yes",
  },
  {
    id: "checkout",
    category: "Billing",
    feature: "Global merchant-of-record checkout",
    starter: "yes",
    pro: "yes",
    enterprise: "yes",
  },
];

export const WORKFLOW_COMPARISON = [
  {
    id: "fragmented",
    title: "Typical multi-tool stack",
    points: [
      "Separate apps for lyrics, image gen, video, and editing",
      "Face consistency breaks between tools",
      "Manual exports and re-uploads at every step",
      "Opaque token pricing across vendors",
    ],
  },
  {
    id: "rtas",
    title: "RTAS Studio AI",
    points: [
      "One studio for compose, render, and publish",
      "Identity lock across scenes",
      "No handoffs — drafts stay in your library",
      "Transparent credits: 1 credit = 1 second",
    ],
  },
] as const;

export const FEATURES_HERO_EYEBROW = "Product capabilities";
export const FEATURES_HERO_HEADLINE = "Everything you need to ship identity-locked video.";
export const FEATURES_HERO_SUPPORT =
  "Compare plans side by side — then open Studio or choose pricing with full clarity.";
