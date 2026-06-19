/**
 * Video playback URLs — simulation fallbacks and backend path normalization.
 */

import { getFastApiBase } from "@/lib/backend-client";
import {
  CINEMATIC_SHOWCASE_VIDEO_URL,
  LEGACY_PREVIEW_SAMPLE_URL,
  LOCAL_SHOWCASE_CACHE_PATH,
  LOCAL_SHOWCASE_CATEGORY_VIDEOS,
  PRIMARY_SHOWCASE_STREAM_URL,
} from "@/lib/preview-showcase";

/** Local path when `npm run fetch:preview` has cached the showcase. */
export const LOCAL_SAMPLE_VIDEO_URL = LOCAL_SHOWCASE_CACHE_PATH;

/** Default cinematic showcase — cyber rap urban stream. */
export const DEFAULT_SHOWCASE_URL = CINEMATIC_SHOWCASE_VIDEO_URL;

function resolveShowcaseUrl(): string {
  return PRIMARY_SHOWCASE_STREAM_URL;
}

function isShowcasePath(url: string): boolean {
  const u = url.trim().toLowerCase();
  if (u === LOCAL_SHOWCASE_CACHE_PATH.toLowerCase()) return true;
  if (u === LEGACY_PREVIEW_SAMPLE_URL.toLowerCase()) return true;
  if (u === CINEMATIC_SHOWCASE_VIDEO_URL.toLowerCase()) return true;
  if (u === PRIMARY_SHOWCASE_STREAM_URL.toLowerCase()) return true;
  return LOCAL_SHOWCASE_CATEGORY_VIDEOS.some(
    (local) => u === local.toLowerCase()
  );
}

/** Local showcase loops for playback fallback. */
export const REMOTE_SAMPLE_VIDEO_URLS = [...LOCAL_SHOWCASE_CATEGORY_VIDEOS] as const;

/** Legacy / remote placeholders mapped to the cinematic showcase. */
export const SIMULATION_PLACEHOLDER_URLS = [
  LEGACY_PREVIEW_SAMPLE_URL,
  "https://www.w3schools.com/html/mov_bbb.mp4",
  "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
  "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
  ...REMOTE_SAMPLE_VIDEO_URLS,
] as const;

export function isSimulationPlaceholderUrl(url: string): boolean {
  const u = url.trim().toLowerCase();
  if (!u) return false;
  if (u === LOCAL_SAMPLE_VIDEO_URL.toLowerCase()) return true;
  if (u === LEGACY_PREVIEW_SAMPLE_URL.toLowerCase()) return true;
  return SIMULATION_PLACEHOLDER_URLS.some((placeholder) => {
    const p = placeholder.toLowerCase();
    return u === p || u.startsWith(p);
  });
}

export function getVideoFallbackChain(primary?: string): string[] {
  const chain: string[] = [];
  const add = (url: string | undefined) => {
    const u = url?.trim();
    if (u && !chain.includes(u)) chain.push(u);
  };

  add(primary);
  for (const local of LOCAL_SHOWCASE_CATEGORY_VIDEOS) add(local);
  add(DEFAULT_SHOWCASE_URL);
  add(PRIMARY_SHOWCASE_STREAM_URL);
  add(LOCAL_SAMPLE_VIDEO_URL);
  for (const sample of REMOTE_SAMPLE_VIDEO_URLS) add(sample);

  return chain;
}

export function isNonPlayablePath(url: string): boolean {
  const u = url.trim();
  if (!u) return true;
  if (/^[a-zA-Z]:[\\/]/.test(u)) return true;
  if (u.startsWith("file://")) return true;
  if (/^data[/\\]uploads/i.test(u)) return true;
  if (/^data[/\\]outputs/i.test(u)) return true;
  return false;
}

export function isBackendOutputUrl(url: string): boolean {
  return /\/media\/outputs\//i.test(url) || /\/outputs\/job_/i.test(url);
}

export type ResolvePlaybackOptions = {
  simulationMode?: boolean;
  preferSample?: boolean;
};

export function resolveVideoPlaybackUrl(
  url: string | undefined,
  options: ResolvePlaybackOptions = {}
): string {
  if (options.simulationMode || options.preferSample) {
    return resolveShowcaseUrl();
  }

  const trimmed = url?.trim() ?? "";
  if (!trimmed || isNonPlayablePath(trimmed)) {
    return resolveShowcaseUrl();
  }

  if (trimmed.startsWith("/video/")) {
    if (isShowcasePath(trimmed)) {
      return resolveShowcaseUrl();
    }
    return trimmed;
  }

  if (/^https?:\/\//i.test(trimmed)) {
    if (isSimulationPlaceholderUrl(trimmed)) {
      return resolveShowcaseUrl();
    }
    return trimmed;
  }

  if (trimmed.startsWith("/")) {
    return `${getFastApiBase()}${trimmed}`;
  }

  const absolute = `${getFastApiBase()}/${trimmed.replace(/^\/+/, "")}`;
  if (isNonPlayablePath(absolute)) {
    return resolveShowcaseUrl();
  }
  return absolute;
}

export function getNextFallback(
  current: string,
  chain: string[] = getVideoFallbackChain(current)
): string | null {
  const idx = chain.indexOf(current);
  if (idx === -1) return chain[0] ?? DEFAULT_SHOWCASE_URL;
  return chain[idx + 1] ?? null;
}

/** True when the player should show the default cinematic showcase (no user render yet). */
export function isShowcasePlayback(
  src: string | undefined,
  resolved: string
): boolean {
  if (!src?.trim()) return true;
  return (
    resolved === DEFAULT_SHOWCASE_URL ||
    isShowcasePath(resolved) ||
    isSimulationPlaceholderUrl(src) ||
    isSimulationPlaceholderUrl(resolved)
  );
}
