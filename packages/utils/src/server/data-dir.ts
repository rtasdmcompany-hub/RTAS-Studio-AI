/**
 * Runtime detection for Vercel/AWS Lambda (read-only filesystem except /tmp).
 * User/auth data must use {@link persistent-store} (Vercel KV), not local files.
 */
export function isServerlessRuntime(): boolean {
  if (process.env.VERCEL === "1" || process.env.VERCEL === "true") return true;
  if (process.env.VERCEL_ENV === "production" || process.env.VERCEL_ENV === "preview") {
    return true;
  }
  if (process.env.AWS_LAMBDA_FUNCTION_NAME) return true;
  const cwd = process.cwd();
  return cwd.startsWith("/var/task") || cwd.startsWith("/vercel/path");
}
