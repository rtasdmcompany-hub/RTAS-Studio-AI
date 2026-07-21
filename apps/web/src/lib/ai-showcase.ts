/**
 * AI Showcase — public proof of output categories.
 * Videos live in apps/web/public/showcase/*.mp4
 */

export type ShowcaseItem = {
  id: string;
  title: string;
  blurb: string;
  src: string;
  audience: string;
};

export const AI_SHOWCASE_ITEMS: ShowcaseItem[] = [
  {
    id: "rap",
    title: "Rap & urban music video",
    blurb: "Lyric-synced performance energy with Identity Preservation on the beat.",
    src: "/showcase/rap.mp4",
    audience: "Artists & rappers",
  },
  {
    id: "solo",
    title: "Solo narrative",
    blurb: "Talking-head and story clips with consistent likeness across cuts.",
    src: "/showcase/solo.mp4",
    audience: "Creators & podcasts",
  },
  {
    id: "commercial",
    title: "Commercial & brand",
    blurb: "Product and promo pacing built for ads that need to ship this week.",
    src: "/showcase/commercial.mp4",
    audience: "Brands & agencies",
  },
  {
    id: "cartoon",
    title: "Stylized animation",
    blurb: "Cartoon and stylized storytelling without leaving the same studio.",
    src: "/showcase/cartoon.mp4",
    audience: "Kids & stylized content",
  },
  {
    id: "islamic",
    title: "Faith-forward cinema",
    blurb: "Respectful cinematic storytelling for culturally specific briefs.",
    src: "/showcase/islamic.mp4",
    audience: "Faith & culture",
  },
];

export const AI_SHOWCASE_HERO_EYEBROW = "AI Showcase";
export const AI_SHOWCASE_HERO_HEADLINE =
  "See Identity Preservation video across the styles you ship.";
export const AI_SHOWCASE_HERO_SUPPORT =
  "Real category loops from the RTAS Studio AI pipeline — mute autoplay previews. Open Studio to create your own.";

export const AI_SHOWCASE_PROOF_POINTS = [
  {
    id: "identity",
    title: "Identity Preservation",
    body: "Likeness stays consistent shot after shot — the core differentiator vs fragmented tools.",
  },
  {
    id: "pipeline",
    title: "One pipeline",
    body: "Compose, render, and publish in a single studio. No re-upload handoffs between apps.",
  },
  {
    id: "credits",
    title: "Honest credits",
    body: "1 credit = 1 second of finished video. What you see in the showcase is what the product ships.",
  },
] as const;
