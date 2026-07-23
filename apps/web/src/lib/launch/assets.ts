/**
 * Phase 13 Sprint 9 — Launch Asset Library inventory.
 * Link real assets when present; label placeholders honestly.
 */

import type { LaunchAsset } from "./types";

export const LAUNCH_ASSETS: LaunchAsset[] = [
  {
    id: "logo-svg",
    title: "Primary logo (SVG)",
    kind: "logo",
    href: "/logo.svg",
    placeholder: false,
    notes: "Verified in public/ — headers, footer, and downloads.",
  },
  {
    id: "logo-png",
    title: "Primary logo (PNG lockup)",
    kind: "logo",
    href: null,
    placeholder: true,
    notes: "Placeholder — see public/logo.png.placeholder.txt. Add rtas-logo.png when ready.",
  },
  {
    id: "favicon",
    title: "Favicon / app icon",
    kind: "logo",
    href: null,
    placeholder: true,
    notes: "Placeholder until rtas-favicon.png is committed to public/.",
  },
  {
    id: "og-image",
    title: "Open Graph share image",
    kind: "media_kit",
    href: "/og-image.png",
    placeholder: true,
    notes:
      "Referenced by metadata; file may be deploy-only. Confirm presence before press sends.",
  },
  {
    id: "group-logo",
    title: "RTAS Group mark",
    kind: "logo",
    href: "/rtas-group-logo.png",
    placeholder: true,
    notes: "Expected at public/rtas-group-logo.png when available.",
  },
  {
    id: "showcase-videos",
    title: "Showcase demo videos",
    kind: "video",
    href: "/showcase",
    placeholder: false,
    notes: "Public showcase route. Individual MP4s live under public/showcase/ when present.",
  },
  {
    id: "studio-screenshots",
    title: "Studio UI screenshots",
    kind: "screenshot",
    href: null,
    placeholder: true,
    notes: "Placeholder — capture compose / render / publish screens for press kit.",
  },
  {
    id: "demo-link",
    title: "Schedule demo",
    kind: "demo",
    href: "/demo",
    placeholder: false,
    notes: "Live commercial demo request flow.",
  },
  {
    id: "media-kit",
    title: "Media kit (ZIP)",
    kind: "media_kit",
    href: null,
    placeholder: true,
    notes: "Placeholder — package logos + screenshots + boilerplate when assets ready.",
  },
  {
    id: "founder-bio",
    title: "Founder bio (short)",
    kind: "founder_bio",
    href: "/about",
    placeholder: false,
    notes: "Public company/about narrative. Dedicated headshot still placeholder.",
  },
  {
    id: "press-kit-guide",
    title: "Press kit guide",
    kind: "press_kit",
    href: null,
    placeholder: false,
    notes: "Documentation: docs/launch/PRESS_KIT_GUIDE.md (repo). Public summary on /launch/assets.",
  },
  {
    id: "brand-guidelines",
    title: "Enterprise brand guidelines",
    kind: "brand_guidelines",
    href: null,
    placeholder: false,
    notes: "marketing/enterprise-brand-guide.md + design tokens — Verified vs Proposed labeled.",
  },
  {
    id: "pricing-onepager",
    title: "Sales one-pager",
    kind: "other",
    href: null,
    placeholder: false,
    notes: "docs/launch/SALES-ONE-PAGER.md — internal/sales use.",
  },
];

export const ASSET_KIND_LABEL: Record<LaunchAsset["kind"], string> = {
  logo: "Logo",
  screenshot: "Screenshot",
  video: "Video",
  demo: "Demo",
  media_kit: "Media kit",
  founder_bio: "Founder bio",
  press_kit: "Press kit",
  brand_guidelines: "Brand guidelines",
  other: "Other",
};
