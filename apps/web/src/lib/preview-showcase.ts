/**
 * Local cinematic loops — apps/web/public/showcase/*.mp4
 * Used on landing hero, category cards, and studio ambient background.
 */

/** Owner can drop a custom MP4 here to override the built-in stream. */
export const STUDIO_DEMO_VIDEO_URL = "/video/rtas-studio-demo.mp4";

/** Optional legacy cache path (npm run fetch:preview). */
export const LOCAL_SHOWCASE_CACHE_PATH = "/video/preview-showcase.mp4";

/** Premium category showcase loops (landing + studio). */
export const LOCAL_SHOWCASE_CATEGORY_VIDEOS = [
  "/showcase/rap.mp4",
  "/showcase/solo.mp4",
  "/showcase/commercial.mp4",
  "/showcase/cartoon.mp4",
  "/showcase/islamic.mp4",
] as const;

/** Returns null — site uses GlobalShowcaseVideoBackground in root layout. */
export function getPageBackgroundVideo(_pathname: string): string | null {
  return null;
}

/** @deprecated Remote fallbacks removed — use LOCAL_SHOWCASE_CATEGORY_VIDEOS. */
export const CINEMATIC_SHOWCASE_REMOTE_URLS = [] as const;

/** Landing hero + studio ambient — local loops only. */
export const LANDING_HERO_VIDEO_SOURCES = LOCAL_SHOWCASE_CATEGORY_VIDEOS;

/** Default preview stream. */
export const PRIMARY_SHOWCASE_STREAM_URL = LOCAL_SHOWCASE_CATEGORY_VIDEOS[0];

/** Default showcase URL used across studio preview player. */
export const CINEMATIC_SHOWCASE_VIDEO_URL = LOCAL_SHOWCASE_CATEGORY_VIDEOS[0];

/** @deprecated Use CINEMATIC_SHOWCASE_VIDEO_URL */
export const LEGACY_PREVIEW_SAMPLE_URL = "/video/preview-sample.mp4";

export const SHOWCASE_HERO_HEADLINE =
  "Direct Videos That Drop Beats & Lock Identities.";

export const SHOWCASE_HERO_TAGLINE =
  "The premium AI music-video studio for rappers and creators — cinematic urban renders, neon concert energy, and identity-locked faces synced to your beat.";

export const SHOWCASE_BADGE_TITLE = "Cyber Rap Preview";

export const SHOWCASE_BADGE_SUBTITLE =
  "Moody urban atmosphere — your renders hit this production tier.";
