/**
 * Observability hooks — structured logging + optional Sentry/analytics.
 * No secrets. Safe no-ops until NEXT_PUBLIC_SENTRY_DSN / analytics IDs are set.
 */

export type LogLevel = "debug" | "info" | "warn" | "error";

export type LogContext = Record<string, string | number | boolean | null | undefined>;

function readPublic(key: string): string {
  const raw = process.env[key];
  return raw?.trim() ?? "";
}

/** True when a Sentry DSN is configured (client or server). */
export function isSentryConfigured(): boolean {
  return Boolean(
    readPublic("NEXT_PUBLIC_SENTRY_DSN") || readPublic("SENTRY_DSN")
  );
}

/** True when a product analytics ID is configured. */
export function isAnalyticsConfigured(): boolean {
  return Boolean(
    readPublic("NEXT_PUBLIC_ANALYTICS_ID") ||
      readPublic("NEXT_PUBLIC_POSTHOG_KEY") ||
      readPublic("NEXT_PUBLIC_GA_MEASUREMENT_ID")
  );
}

export function getObservabilityStatus(): {
  sentry: boolean;
  analytics: boolean;
  environment: string;
} {
  return {
    sentry: isSentryConfigured(),
    analytics: isAnalyticsConfigured(),
    environment: process.env.NODE_ENV || "development",
  };
}

function serializeContext(ctx?: LogContext): string {
  if (!ctx || Object.keys(ctx).length === 0) return "";
  try {
    return ` ${JSON.stringify(ctx)}`;
  } catch {
    return "";
  }
}

/** Structured console logger — replace sink with Sentry/Datadog when wired. */
export function logEvent(
  level: LogLevel,
  message: string,
  context?: LogContext
): void {
  const line = `[rtas:${level}] ${message}${serializeContext(context)}`;
  if (level === "error") console.error(line);
  else if (level === "warn") console.warn(line);
  else if (level === "debug" && process.env.NODE_ENV !== "production") {
    console.debug(line);
  } else console.info(line);
}

/**
 * Capture an error for ops. Currently logs structured JSON.
 * When NEXT_PUBLIC_SENTRY_DSN is set, integrate @sentry/nextjs and forward here.
 */
export function captureException(
  error: unknown,
  context?: LogContext
): void {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : "Unknown error";
  const stack = error instanceof Error ? error.stack : undefined;
  logEvent("error", message, {
    ...context,
    stack: stack ? "present" : undefined,
    sentryConfigured: isSentryConfigured(),
  });
}

/** Timing helper for API route performance metrics (logs duration_ms). */
export async function withTiming<T>(
  name: string,
  fn: () => Promise<T>,
  context?: LogContext
): Promise<T> {
  const start = Date.now();
  try {
    const result = await fn();
    logEvent("info", `timing:${name}`, {
      ...context,
      duration_ms: Date.now() - start,
      ok: true,
    });
    return result;
  } catch (err) {
    logEvent("error", `timing:${name}`, {
      ...context,
      duration_ms: Date.now() - start,
      ok: false,
    });
    captureException(err, { ...context, op: name });
    throw err;
  }
}

/** Client-safe analytics stub — no-op until IDs are configured. */
export function trackEvent(
  event: string,
  properties?: LogContext
): void {
  if (!isAnalyticsConfigured()) {
    if (process.env.NODE_ENV !== "production") {
      logEvent("debug", `analytics:${event}`, properties);
    }
    return;
  }
  logEvent("info", `analytics:${event}`, {
    ...properties,
    analyticsConfigured: true,
  });
}
