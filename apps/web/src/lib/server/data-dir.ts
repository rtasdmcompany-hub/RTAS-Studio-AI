import os from "os";
import path from "path";

/**
 * Writable data directory for JSON file stores.
 * - Local dev: `<cwd>/.data`
 * - Vercel/serverless: `/tmp/rtas-studio-data` (cwd is read-only under /var/task)
 */
export function getServerDataDir(): string {
  const override = process.env.RTAS_DATA_DIR?.trim();
  if (override) return override;

  if (process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME) {
    return path.join(os.tmpdir(), "rtas-studio-data");
  }

  return path.join(process.cwd(), ".data");
}
