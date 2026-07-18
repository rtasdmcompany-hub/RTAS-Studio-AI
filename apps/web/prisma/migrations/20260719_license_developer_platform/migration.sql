-- Phase 8 Sprint 7 — Enterprise License, API Access & Developer Platform (UP)

CREATE TABLE IF NOT EXISTS "Licenses" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "licenseKey" TEXT NOT NULL UNIQUE,
  "tier" TEXT NOT NULL DEFAULT 'free',
  "status" TEXT NOT NULL DEFAULT 'active',
  "activatedAt" TIMESTAMP(3),
  "expiresAt" TIMESTAMP(3),
  "suspendedAt" TIMESTAMP(3),
  "revokedAt" TIMESTAMP(3),
  "activatedBy" TEXT,
  "seats" INTEGER NOT NULL DEFAULT 1,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Licenses_organizationId_idx" ON "Licenses"("organizationId");
CREATE INDEX IF NOT EXISTS "Licenses_tier_idx" ON "Licenses"("tier");
CREATE INDEX IF NOT EXISTS "Licenses_status_idx" ON "Licenses"("status");

CREATE TABLE IF NOT EXISTS "LicenseHistory" (
  "id" TEXT PRIMARY KEY,
  "licenseId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "tier" TEXT NOT NULL DEFAULT '',
  "detail" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LicenseHistory_licenseId_idx" ON "LicenseHistory"("licenseId");
CREATE INDEX IF NOT EXISTS "LicenseHistory_organizationId_createdAt_idx"
  ON "LicenseHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "LicenseHistory_action_idx" ON "LicenseHistory"("action");

CREATE TABLE IF NOT EXISTS "ApiKeys" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "keyType" TEXT NOT NULL DEFAULT 'personal',
  "access" TEXT NOT NULL DEFAULT 'full_access',
  "name" TEXT NOT NULL DEFAULT '',
  "keyPrefix" TEXT NOT NULL DEFAULT '',
  "keyHash" TEXT NOT NULL UNIQUE,
  "scopesJson" JSONB,
  "ownerUserId" TEXT,
  "workspaceId" TEXT,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "lastUsedAt" TIMESTAMP(3),
  "rotatedAt" TIMESTAMP(3),
  "revokedAt" TIMESTAMP(3),
  "expiresAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ApiKeys_organizationId_idx" ON "ApiKeys"("organizationId");
CREATE INDEX IF NOT EXISTS "ApiKeys_ownerUserId_idx" ON "ApiKeys"("ownerUserId");
CREATE INDEX IF NOT EXISTS "ApiKeys_workspaceId_idx" ON "ApiKeys"("workspaceId");
CREATE INDEX IF NOT EXISTS "ApiKeys_keyType_idx" ON "ApiKeys"("keyType");
CREATE INDEX IF NOT EXISTS "ApiKeys_active_idx" ON "ApiKeys"("active");

CREATE TABLE IF NOT EXISTS "PersonalAccessTokens" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "name" TEXT NOT NULL DEFAULT '',
  "tokenPrefix" TEXT NOT NULL DEFAULT '',
  "tokenHash" TEXT NOT NULL UNIQUE,
  "scopesJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "lastUsedAt" TIMESTAMP(3),
  "revokedAt" TIMESTAMP(3),
  "expiresAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PersonalAccessTokens_userId_idx" ON "PersonalAccessTokens"("userId");
CREATE INDEX IF NOT EXISTS "PersonalAccessTokens_organizationId_idx" ON "PersonalAccessTokens"("organizationId");
CREATE INDEX IF NOT EXISTS "PersonalAccessTokens_active_idx" ON "PersonalAccessTokens"("active");

CREATE TABLE IF NOT EXISTS "ApiUsage" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "apiKeyId" TEXT,
  "workspaceId" TEXT,
  "endpoint" TEXT NOT NULL DEFAULT '',
  "method" TEXT NOT NULL DEFAULT 'GET',
  "statusCode" INTEGER NOT NULL DEFAULT 200,
  "latencyMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ApiUsage_organizationId_createdAt_idx"
  ON "ApiUsage"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ApiUsage_apiKeyId_idx" ON "ApiUsage"("apiKeyId");
CREATE INDEX IF NOT EXISTS "ApiUsage_endpoint_idx" ON "ApiUsage"("endpoint");

CREATE TABLE IF NOT EXISTS "RateLimits" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "scope" TEXT NOT NULL DEFAULT 'organization',
  "scopeId" TEXT NOT NULL,
  "tier" TEXT NOT NULL DEFAULT 'free',
  "perMinute" INTEGER NOT NULL DEFAULT 0,
  "perHour" INTEGER NOT NULL DEFAULT 0,
  "perDay" INTEGER NOT NULL DEFAULT 0,
  "minuteWindow" TEXT NOT NULL DEFAULT '',
  "minuteCount" INTEGER NOT NULL DEFAULT 0,
  "hourWindow" TEXT NOT NULL DEFAULT '',
  "hourCount" INTEGER NOT NULL DEFAULT 0,
  "dayWindow" TEXT NOT NULL DEFAULT '',
  "dayCount" INTEGER NOT NULL DEFAULT 0,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RateLimits_scope_scopeId_key" UNIQUE ("scope", "scopeId")
);
CREATE INDEX IF NOT EXISTS "RateLimits_organizationId_idx" ON "RateLimits"("organizationId");
CREATE INDEX IF NOT EXISTS "RateLimits_tier_idx" ON "RateLimits"("tier");

CREATE TABLE IF NOT EXISTS "Webhooks" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "url" TEXT NOT NULL,
  "eventsJson" JSONB,
  "secretHash" TEXT NOT NULL DEFAULT '',
  "secretPrefix" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdBy" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Webhooks_organizationId_idx" ON "Webhooks"("organizationId");
CREATE INDEX IF NOT EXISTS "Webhooks_active_idx" ON "Webhooks"("active");

CREATE TABLE IF NOT EXISTS "WebhookDeliveries" (
  "id" TEXT PRIMARY KEY,
  "webhookId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "payloadJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "attempts" INTEGER NOT NULL DEFAULT 0,
  "lastError" TEXT NOT NULL DEFAULT '',
  "nextRetryAt" TIMESTAMP(3),
  "deliveredAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "WebhookDeliveries_webhookId_createdAt_idx"
  ON "WebhookDeliveries"("webhookId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "WebhookDeliveries_organizationId_idx" ON "WebhookDeliveries"("organizationId");
CREATE INDEX IF NOT EXISTS "WebhookDeliveries_status_idx" ON "WebhookDeliveries"("status");
CREATE INDEX IF NOT EXISTS "WebhookDeliveries_eventType_idx" ON "WebhookDeliveries"("eventType");
