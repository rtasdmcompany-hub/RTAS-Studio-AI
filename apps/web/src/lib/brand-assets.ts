/** Circular hexagon mark — use with BrandLockup text beside it. */
export const BRAND_FAVICON_PATH = "/rtas-favicon.png";
export const BRAND_LOGO_PATH = "/rtas-logo.png";

/** Default rendered logo dimensions (prevents CLS with explicit width/height). */
export const BRAND_LOGO_SIZES = {
  icon: { width: 32, height: 32 },
  mark: { width: 44, height: 44 },
  full: { width: 72, height: 72 },
} as const;

/** Footer subsidiary brand marks — lazy-loaded below the fold. */
export const FOOTER_BRAND_LOGO_SIZE = { width: 34, height: 34 } as const;

export const FOOTER_BRAND_LOGO_PATHS = {
  studioAi: "/footer-logo-studio-ai.png",
  digitalMarketing: "/footer-logo-digital-marketing.png",
  group: "/footer-logo-group.png",
} as const;
