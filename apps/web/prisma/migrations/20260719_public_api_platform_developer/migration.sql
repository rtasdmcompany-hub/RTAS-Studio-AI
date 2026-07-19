-- Phase 9 Sprint 6 — Public API Platform, SDK & Developer Ecosystem (UP)

CREATE TABLE IF NOT EXISTS "DeveloperAccounts" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "displayName" TEXT NOT NULL,
  "email" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'active',
  "company" TEXT NOT NULL DEFAULT '',
  "website" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "DeveloperAccounts_userId_organizationId_key" UNIQUE ("userId", "organizationId"),
  CONSTRAINT "DeveloperAccounts_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "DeveloperAccounts_organizationId_idx" ON "DeveloperAccounts"("organizationId");
CREATE INDEX IF NOT EXISTS "DeveloperAccounts_status_idx" ON "DeveloperAccounts"("status");

CREATE TABLE IF NOT EXISTS "ApiApplications" (
  "id" TEXT PRIMARY KEY,
  "developerId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'active',
  "homepageUrl" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ApiApplications_developerId_fkey" FOREIGN KEY ("developerId")
    REFERENCES "DeveloperAccounts"("id") ON DELETE CASCADE,
  CONSTRAINT "ApiApplications_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "ApiApplications_developerId_idx" ON "ApiApplications"("developerId");
CREATE INDEX IF NOT EXISTS "ApiApplications_organizationId_idx" ON "ApiApplications"("organizationId");
CREATE INDEX IF NOT EXISTS "ApiApplications_slug_idx" ON "ApiApplications"("slug");

CREATE TABLE IF NOT EXISTS "OAuthClients" (
  "id" TEXT PRIMARY KEY,
  "developerId" TEXT NOT NULL,
  "applicationId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "clientId" TEXT NOT NULL,
  "clientSecretHash" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "redirectUrisJson" JSONB,
  "grantTypesJson" JSONB,
  "scopesJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'active',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "OAuthClients_clientId_key" UNIQUE ("clientId"),
  CONSTRAINT "OAuthClients_developerId_fkey" FOREIGN KEY ("developerId")
    REFERENCES "DeveloperAccounts"("id") ON DELETE CASCADE,
  CONSTRAINT "OAuthClients_applicationId_fkey" FOREIGN KEY ("applicationId")
    REFERENCES "ApiApplications"("id") ON DELETE CASCADE,
  CONSTRAINT "OAuthClients_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "OAuthClients_developerId_idx" ON "OAuthClients"("developerId");
CREATE INDEX IF NOT EXISTS "OAuthClients_applicationId_idx" ON "OAuthClients"("applicationId");
CREATE INDEX IF NOT EXISTS "OAuthClients_organizationId_idx" ON "OAuthClients"("organizationId");
CREATE INDEX IF NOT EXISTS "OAuthClients_status_idx" ON "OAuthClients"("status");

CREATE TABLE IF NOT EXISTS "ApiTokens" (
  "id" TEXT PRIMARY KEY,
  "developerId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "applicationId" TEXT,
  "workspaceId" TEXT,
  "name" TEXT NOT NULL,
  "tokenPrefix" TEXT NOT NULL,
  "tokenHash" TEXT NOT NULL,
  "scopesJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'active',
  "rateLimitPerMinute" INTEGER NOT NULL DEFAULT 120,
  "lastUsedAt" TIMESTAMP(3),
  "expiresAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "revokedAt" TIMESTAMP(3),
  CONSTRAINT "ApiTokens_tokenHash_key" UNIQUE ("tokenHash"),
  CONSTRAINT "ApiTokens_developerId_fkey" FOREIGN KEY ("developerId")
    REFERENCES "DeveloperAccounts"("id") ON DELETE CASCADE,
  CONSTRAINT "ApiTokens_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "ApiTokens_applicationId_fkey" FOREIGN KEY ("applicationId")
    REFERENCES "ApiApplications"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "ApiTokens_developerId_idx" ON "ApiTokens"("developerId");
CREATE INDEX IF NOT EXISTS "ApiTokens_organizationId_idx" ON "ApiTokens"("organizationId");
CREATE INDEX IF NOT EXISTS "ApiTokens_workspaceId_idx" ON "ApiTokens"("workspaceId");
CREATE INDEX IF NOT EXISTS "ApiTokens_status_idx" ON "ApiTokens"("status");

CREATE TABLE IF NOT EXISTS "ApiVersions" (
  "id" TEXT PRIMARY KEY,
  "version" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'active',
  "changelog" TEXT NOT NULL DEFAULT '',
  "deprecatedAt" TIMESTAMP(3),
  "sunsetAt" TIMESTAMP(3),
  "compatibilityJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ApiVersions_version_key" UNIQUE ("version")
);
CREATE INDEX IF NOT EXISTS "ApiVersions_status_idx" ON "ApiVersions"("status");

CREATE TABLE IF NOT EXISTS "ApiUsageLogs" (
  "id" TEXT PRIMARY KEY,
  "developerId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "tokenId" TEXT,
  "clientId" TEXT,
  "surface" TEXT NOT NULL,
  "method" TEXT NOT NULL,
  "path" TEXT NOT NULL,
  "statusCode" INTEGER NOT NULL DEFAULT 200,
  "latencyMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "version" TEXT NOT NULL DEFAULT 'v1',
  "workspaceId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ApiUsageLogs_developerId_fkey" FOREIGN KEY ("developerId")
    REFERENCES "DeveloperAccounts"("id") ON DELETE CASCADE,
  CONSTRAINT "ApiUsageLogs_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "ApiUsageLogs_tokenId_fkey" FOREIGN KEY ("tokenId")
    REFERENCES "ApiTokens"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "ApiUsageLogs_developerId_createdAt_idx"
  ON "ApiUsageLogs"("developerId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ApiUsageLogs_organizationId_idx" ON "ApiUsageLogs"("organizationId");
CREATE INDEX IF NOT EXISTS "ApiUsageLogs_surface_idx" ON "ApiUsageLogs"("surface");
CREATE INDEX IF NOT EXISTS "ApiUsageLogs_tokenId_idx" ON "ApiUsageLogs"("tokenId");

CREATE TABLE IF NOT EXISTS "SdkReleases" (
  "id" TEXT PRIMARY KEY,
  "language" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "packageName" TEXT NOT NULL,
  "downloadUrl" TEXT NOT NULL DEFAULT '',
  "checksum" TEXT NOT NULL DEFAULT '',
  "changelog" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'published',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "SdkReleases_language_version_key" UNIQUE ("language", "version")
);
CREATE INDEX IF NOT EXISTS "SdkReleases_language_idx" ON "SdkReleases"("language");
CREATE INDEX IF NOT EXISTS "SdkReleases_status_idx" ON "SdkReleases"("status");

CREATE TABLE IF NOT EXISTS "WebhookSubscriptions" (
  "id" TEXT PRIMARY KEY,
  "developerId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "applicationId" TEXT,
  "targetUrl" TEXT NOT NULL,
  "eventsJson" JSONB,
  "secretHash" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'active',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "WebhookSubscriptions_developerId_fkey" FOREIGN KEY ("developerId")
    REFERENCES "DeveloperAccounts"("id") ON DELETE CASCADE,
  CONSTRAINT "WebhookSubscriptions_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "WebhookSubscriptions_applicationId_fkey" FOREIGN KEY ("applicationId")
    REFERENCES "ApiApplications"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "WebhookSubscriptions_developerId_idx" ON "WebhookSubscriptions"("developerId");
CREATE INDEX IF NOT EXISTS "WebhookSubscriptions_organizationId_idx" ON "WebhookSubscriptions"("organizationId");
CREATE INDEX IF NOT EXISTS "WebhookSubscriptions_status_idx" ON "WebhookSubscriptions"("status");
