import { isServerlessRuntime } from "@rtas/utils/server";

const PLACEHOLDER_SECRETS = new Set([
  "",
  "generate-with-openssl-rand-base64-32",
  "your-random-secret-here",
  "change-me",
]);

function readEnv(key: string): string {
  const raw = process.env[key];
  if (raw === undefined || raw === null) return "";
  let value = raw.trim();
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1).trim();
  }
  if (value.charCodeAt(0) === 0xfeff) {
    value = value.slice(1);
  }
  return value;
}

function isRealSecret(value: string): boolean {
  return value.length > 0 && !PLACEHOLDER_SECRETS.has(value);
}

export function getNextAuthSecret(): string {
  const secret = readEnv("NEXTAUTH_SECRET");
  if (isRealSecret(secret)) return secret;
  if (process.env.NODE_ENV === "development") {
    return "rtas-omni-dev-insecure-nextauth-secret-run-setup";
  }
  return "rtas-omni-production-placeholder-run-setup";
}

export function getNextAuthUrl(): string {
  return readEnv("NEXTAUTH_URL") || readEnv("NEXT_PUBLIC_APP_URL") || "http://localhost:3001";
}

export function getGoogleClientId(): string {
  return readEnv("GOOGLE_CLIENT_ID") || readEnv("AUTH_GOOGLE_ID");
}

export function getGoogleClientSecret(): string {
  return readEnv("GOOGLE_CLIENT_SECRET") || readEnv("AUTH_GOOGLE_SECRET");
}

export function isGoogleAuthConfigured(): boolean {
  const id = getGoogleClientId();
  const secret = getGoogleClientSecret();
  return id.length > 0 && secret.length > 0 && id.includes(".apps.googleusercontent.com");
}

export function isEmailDeliveryConfigured(): boolean {
  return process.env.NODE_ENV === "development" || !isServerlessRuntime();
}
