import type { AnalyticsProps } from "./events";

const BLOCKED_KEYS = new Set([
  "password",
  "token",
  "secret",
  "authorization",
  "apiKey",
  "api_key",
  "webhookSecret",
  "client_secret",
  "accessToken",
  "refreshToken",
  "card",
  "cvv",
  "ssn",
]);

/**
 * Strip secrets / high-risk keys. Truncate long strings. Never log full PII dumps.
 */
export function sanitizeAnalyticsProps(
  properties?: AnalyticsProps
): AnalyticsProps | undefined {
  if (!properties) return undefined;
  const out: AnalyticsProps = {};
  for (const [key, value] of Object.entries(properties)) {
    const lower = key.toLowerCase();
    if (
      BLOCKED_KEYS.has(key) ||
      BLOCKED_KEYS.has(lower) ||
      lower.includes("password") ||
      lower.includes("secret") ||
      lower.includes("token")
    ) {
      continue;
    }
    if (typeof value === "string") {
      out[key] = value.length > 200 ? `${value.slice(0, 200)}…` : value;
    } else {
      out[key] = value;
    }
  }
  return out;
}
