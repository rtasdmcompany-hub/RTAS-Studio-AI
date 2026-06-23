export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { validateProductionServerEnv } = await import("@/lib/env");
    validateProductionServerEnv();
  }
}
