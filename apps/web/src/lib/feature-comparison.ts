/**
 * Feature comparison — plan matrix + workflow contrast.
 * Public marketing must stay Paddle AUP compliant (no face-swap / deepfake claims).
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

/** Public capability cards — compliant product positioning only */
export const FEATURE_CAPABILITIES = [
  {
    id: "text-to-video",
    title: "Text to Video",
    body: "Turn scripts and prompts into cinematic clips in one studio.",
  },
  {
    id: "image-to-video",
    title: "Image to Video",
    body: "Animate stills into motion for ads, social, and storyboards.",
  },
  {
    id: "ai-video",
    title: "AI Video Generation",
    body: "Cloud GPU pipeline with live progress from draft to master.",
  },
  {
    id: "commercials",
    title: "Product Commercials",
    body: "Ship brand spots and product showcases without a multi-tool stack.",
  },
  {
    id: "marketing",
    title: "Marketing Videos",
    body: "Campaign cuts sized for launch pages, email, and paid social.",
  },
  {
    id: "social",
    title: "Social Media Content",
    body: "Vertical and square-ready exports for feeds and stories.",
  },
  {
    id: "music",
    title: "Music Videos",
    body: "Sync lyrics and audio into performance-ready video.",
  },
  {
    id: "animation",
    title: "AI Animation",
    body: "Stylized motion and animated sequences from your prompts.",
  },
  {
    id: "anime",
    title: "Anime",
    body: "Anime-inspired looks for stories and characters you create.",
  },
  {
    id: "3d",
    title: "3D Characters",
    body: "Dimensional character looks for original worlds and scenes.",
  },
  {
    id: "original-ai",
    title: "Original AI Characters",
    body: "Design and reuse original characters across multi-scene projects.",
  },
  {
    id: "avatar",
    title: "Talking Avatar",
    body: "Presenters and avatars for explainers you are authorized to publish.",
  },
  {
    id: "lipsync",
    title: "Lip Sync (User-owned Content)",
    body: "Align mouth motion to audio you own or are licensed to use.",
  },
  {
    id: "upscale",
    title: "Video Upscaling",
    body: "Enhance resolution toward HD and cinematic 4K on paid tiers.",
  },
  {
    id: "bg-remove",
    title: "Background Removal",
    body: "Isolate subjects for composites and clean product plates.",
  },
  {
    id: "enhance",
    title: "Image Enhancement",
    body: "Sharpen and polish stills before animation or export.",
  },
  {
    id: "edit",
    title: "AI Editing",
    body: "Guided edits in-studio — compose, refine, and publish in one place.",
  },
  {
    id: "identity",
    title: "Identity Preservation",
    body: "Authorized Identity Consistency keeps a likeness you own or control consistent across scenes.",
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
    feature: "Authorized Identity Preservation",
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
      "Identity consistency breaks between tools",
      "Manual exports and re-uploads at every step",
      "Opaque token pricing across vendors",
    ],
  },
  {
    id: "rtas",
    title: "RTAS Studio AI",
    points: [
      "One studio for compose, render, and publish",
      "Authorized Identity Preservation across scenes",
      "No handoffs — drafts stay in your library",
      "Transparent credits: 1 credit = 1 second",
    ],
  },
] as const;

export const FEATURES_HERO_EYEBROW = "Product capabilities";
export const FEATURES_HERO_HEADLINE =
  "Everything you need to ship original AI video.";
export const FEATURES_HERO_SUPPORT =
  "Text to video, commercials, music videos, animation, and authorized identity consistency — compare plans, then open Studio.";
