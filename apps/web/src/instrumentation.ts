export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { validateProductionServerEnv } = await import("@/lib/env");
    validateProductionServerEnv();

    const { getObservabilityStatus, logEvent } = await import(
      "@/lib/observability"
    );
    const obs = getObservabilityStatus();
    logEvent("info", "boot:observability", {
      sentry: obs.sentry,
      analytics: obs.analytics,
      environment: obs.environment,
    });
  }
}
