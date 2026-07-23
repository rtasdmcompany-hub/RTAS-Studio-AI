/**
 * Cookie consent helpers shared by CookieConsent UI and client analytics.
 * Storage key must stay in sync with CookieConsent.tsx.
 *
 * Categories: Necessary (always on) · Analytics · Marketing.
 * Legacy values "all" | "essential" remain readable for existing users.
 */

export const COOKIE_CONSENT_KEY = "rtas-cookie-consent";
export const COOKIE_CONSENT_EVENT = "rtas-cookie-consent";
export const COOKIE_PREFS_OPEN_EVENT = "rtas-cookie-prefs-open";

export type CookieCategoryPrefs = {
  necessary: true;
  analytics: boolean;
  marketing: boolean;
};

/** Legacy banner values still accepted from localStorage. */
export type CookieConsentLegacy = "all" | "essential";

export type CookieConsentValue = CookieConsentLegacy | CookieCategoryPrefs;

export const DEFAULT_NECESSARY_ONLY: CookieCategoryPrefs = {
  necessary: true,
  analytics: false,
  marketing: false,
};

export const DEFAULT_ACCEPT_ALL: CookieCategoryPrefs = {
  necessary: true,
  analytics: true,
  marketing: true,
};

function isPrefs(value: unknown): value is CookieCategoryPrefs {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    v.necessary === true &&
    typeof v.analytics === "boolean" &&
    typeof v.marketing === "boolean"
  );
}

export function normalizeCookiePrefs(
  value: CookieConsentValue | null
): CookieCategoryPrefs | null {
  if (!value) return null;
  if (value === "all") return { ...DEFAULT_ACCEPT_ALL };
  if (value === "essential") return { ...DEFAULT_NECESSARY_ONLY };
  if (isPrefs(value)) {
    return {
      necessary: true,
      analytics: value.analytics,
      marketing: value.marketing,
    };
  }
  return null;
}

export function readCookieConsent(): CookieCategoryPrefs | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!raw) return null;
    if (raw === "all" || raw === "essential") {
      return normalizeCookiePrefs(raw);
    }
    const parsed = JSON.parse(raw) as unknown;
    return normalizeCookiePrefs(
      isPrefs(parsed) ? parsed : null
    );
  } catch {
    return null;
  }
}

/** Optional product analytics may run only when Analytics is enabled. */
export function hasAnalyticsConsent(): boolean {
  return readCookieConsent()?.analytics === true;
}

/** Optional marketing / campaign tags may run only when Marketing is enabled. */
export function hasMarketingConsent(): boolean {
  return readCookieConsent()?.marketing === true;
}

export function writeCookieConsent(value: CookieConsentValue): void {
  if (typeof window === "undefined") return;
  const prefs = normalizeCookiePrefs(value);
  if (!prefs) return;
  try {
    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(prefs));
    window.dispatchEvent(
      new CustomEvent(COOKIE_CONSENT_EVENT, { detail: prefs })
    );
  } catch {
    /* ignore quota / private mode */
  }
}

/** Open the cookie preference panel from Privacy settings or Cookie Policy. */
export function openCookiePreferences(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(COOKIE_PREFS_OPEN_EVENT));
}
