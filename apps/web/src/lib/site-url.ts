/** Canonical production origin (apex). All SEO URLs resolve here. */
export const SITE_URL = (
  process.env.NEXT_PUBLIC_APP_URL?.trim() ||
  process.env.NEXTAUTH_URL?.trim() ||
  "https://rtasstudio.com"
).replace(/\/$/, "");

export const SITE_HOST = new URL(SITE_URL).host;

/** Build absolute canonical URL for a path (always apex). */
export function canonicalUrl(path = "/"): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (normalized === "/") return `${SITE_URL}/`;
  return `${SITE_URL}${normalized.replace(/\/$/, "") || ""}`;
}
