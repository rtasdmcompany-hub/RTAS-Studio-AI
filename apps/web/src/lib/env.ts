/**
 * Central environment helpers — empty keys fall back to safe dev/simulation defaults.
 */

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
  // Strip wrapping quotes from copy-paste (common cause of invalid_client)
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1).trim();
  }
  // Strip UTF-8 BOM if present
  if (value.charCodeAt(0) === 0xfeff) {
    value = value.slice(1);
  }
  return value;
}

function isRealSecret(value: string): boolean {
  return value.length > 0 && !PLACEHOLDER_SECRETS.has(value);
}

/** NextAuth signing secret — never throws; dev/build fallbacks when unset. */
export function getNextAuthSecret(): string {
  const secret = readEnv("NEXTAUTH_SECRET");
  if (isRealSecret(secret)) return secret;

  if (process.env.NODE_ENV === "development") {
    return "rtas-dev-insecure-nextauth-secret-run-npm-setup-env";
  }

  return "rtas-production-placeholder-run-npm-setup-env";
}

export function getNextAuthUrl(): string {
  return readEnv("NEXTAUTH_URL") || readEnv("NEXT_PUBLIC_APP_URL") || "http://localhost:3000";
}

export function getGoogleClientId(): string {
  return readEnv("GOOGLE_CLIENT_ID") || readEnv("AUTH_GOOGLE_ID");
}

export function getGoogleClientSecret(): string {
  return readEnv("GOOGLE_CLIENT_SECRET") || readEnv("AUTH_GOOGLE_SECRET");
}

export function getGoogleOAuthCallbackUrl(): string {
  const explicit = readEnv("GOOGLE_OAUTH_REDIRECT_URI");
  if (explicit) return explicit.replace(/\/$/, "");
  const base = getNextAuthUrl().replace(/\/$/, "");
  return `${base}/api/auth/callback/google`;
}

export function getGoogleOAuthJsOrigin(): string {
  const explicit = readEnv("GOOGLE_OAUTH_JS_ORIGIN");
  if (explicit) return explicit.replace(/\/$/, "");
  return getNextAuthUrl().replace(/\/$/, "");
}

export function getGoogleOAuthConsoleSettings(): {
  redirectUris: string[];
  javascriptOrigins: string[];
  callbackUrl: string;
  jsOrigin: string;
} {
  const callbackUrl = getGoogleOAuthCallbackUrl();
  const jsOrigin = getGoogleOAuthJsOrigin();
  const redirectAlt = readEnv("GOOGLE_OAUTH_REDIRECT_URI_ALT");
  const jsAlt = readEnv("GOOGLE_OAUTH_JS_ORIGIN_ALT");

  const redirectUris = [callbackUrl];
  if (redirectAlt && !redirectUris.includes(redirectAlt)) {
    redirectUris.push(redirectAlt.replace(/\/$/, ""));
  }

  const javascriptOrigins = [jsOrigin];
  if (jsAlt && !javascriptOrigins.includes(jsAlt)) {
    javascriptOrigins.push(jsAlt.replace(/\/$/, ""));
  }

  return { redirectUris, javascriptOrigins, callbackUrl, jsOrigin };
}

export function isGoogleAuthConfigured(): boolean {
  const id = getGoogleClientId();
  const secret = getGoogleClientSecret();
  return id.length > 0 && secret.length > 0 && id.includes(".apps.googleusercontent.com");
}

/** Google button + provider when credentials exist; explicit opt-out via env. */
export function isGoogleAuthEnabled(): boolean {
  const explicit = readEnv("NEXT_PUBLIC_GOOGLE_AUTH_ENABLED").toLowerCase();
  if (explicit === "false") return false;
  return isGoogleAuthConfigured();
}

export function isFalConfigured(): boolean {
  return readEnv("FAL_KEY").length > 0;
}

export function isReplicateConfigured(): boolean {
  return readEnv("REPLICATE_API_TOKEN").length > 0;
}

/** True when any supported cloud renderer key is set in this Next.js env. */
export function isCloudAiConfigured(): boolean {
  return isFalConfigured() || isReplicateConfigured();
}

export function isFastApiConfigured(): boolean {
  const url = readEnv("NEXT_PUBLIC_FASTAPI_URL");
  return url.length > 0;
}

export function getSimulationMode(): boolean {
  return !isCloudAiConfigured();
}

export function getResendApiKey(): string {
  return readEnv("RESEND_API_KEY");
}

export function getEmailFrom(): string {
  return (
    readEnv("EMAIL_FROM") ||
    readEnv("SMTP_FROM") ||
    `"RTAS STUDIO AI" <noreply@rtasstudio.ai>`
  );
}

export type SmtpConfig = {
  host: string;
  port: number;
  secure: boolean;
  user: string;
  pass: string;
};

export function getSmtpConfig(): SmtpConfig | null {
  const host = readEnv("SMTP_HOST");
  const user = readEnv("SMTP_USER");
  const pass = readEnv("SMTP_PASS");
  if (!host || !user || !pass) return null;

  const portRaw = readEnv("SMTP_PORT");
  const port = portRaw ? Number(portRaw) : 587;
  const secure =
    readEnv("SMTP_SECURE").toLowerCase() === "true" || port === 465;

  return { host, port, secure, user, pass };
}

import { isServerlessRuntime } from "@/lib/server/data-dir";

export function isEmailDeliveryConfigured(): boolean {
  return Boolean(getResendApiKey() || getSmtpConfig());
}

export function getEmailDeliveryMode():
  | "resend"
  | "smtp"
  | "dev-file"
  | "link-only"
  | "none" {
  if (getResendApiKey()) return "resend";
  if (getSmtpConfig()) return "smtp";
  if (process.env.NODE_ENV === "development") return "dev-file";
  if (isServerlessRuntime()) return "link-only";
  return "none";
}

export type EmailDeliveryMode = ReturnType<typeof getEmailDeliveryMode>;

export function exposesVerificationLinkOnPage(mode: EmailDeliveryMode): boolean {
  return mode === "dev-file" || mode === "link-only";
}

export type PublicRuntimeConfig = {
  googleAuthEnabled: boolean;
  fastApiUrl: string;
  simulationMode: boolean;
  falConfigured: boolean;
  replicateConfigured: boolean;
  googleClientIdSuffix?: string;
  googleClientIdHint?: string;
  googleOAuthCallbackUrl?: string;
  googleOAuthJsOrigin?: string;
  googleOAuthRedirectUris?: string[];
  googleOAuthJavaScriptOrigins?: string[];
};

export function getPublicRuntimeConfig(): PublicRuntimeConfig {
  const fastApiUrl =
    readEnv("NEXT_PUBLIC_FASTAPI_URL") || "http://localhost:8000";
  const clientId = getGoogleClientId();
  const oauth = getGoogleOAuthConsoleSettings();

  return {
    googleAuthEnabled: isGoogleAuthEnabled(),
    fastApiUrl: fastApiUrl.replace(/\/$/, ""),
    simulationMode: getSimulationMode(),
    falConfigured: isFalConfigured(),
    replicateConfigured: isReplicateConfigured(),
    googleClientIdSuffix: clientId ? clientId.slice(-24) : undefined,
    googleClientIdHint: clientId
      ? `${clientId.slice(0, 20)}…${clientId.slice(-24)}`
      : undefined,
    googleOAuthCallbackUrl: isGoogleAuthConfigured()
      ? oauth.callbackUrl
      : undefined,
    googleOAuthJsOrigin: isGoogleAuthConfigured() ? oauth.jsOrigin : undefined,
    googleOAuthRedirectUris: isGoogleAuthConfigured()
      ? oauth.redirectUris
      : undefined,
    googleOAuthJavaScriptOrigins: isGoogleAuthConfigured()
      ? oauth.javascriptOrigins
      : undefined,
  };
}
