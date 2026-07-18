-- Phase 8 Sprint 4 — Credit Consumption, Usage Metering & Quota Engine (UP)

CREATE TABLE IF NOT EXISTS "CreditUsage" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "userId" TEXT,
  "teamId" TEXT,
  "serviceType" TEXT NOT NULL,
  "provider" TEXT NOT NULL DEFAULT 'default',
  "credits" INTEGER NOT NULL,
  "quantity" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "resourceType" TEXT,
  "resourceId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'completed',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CreditUsage_organizationId_createdAt_idx"
  ON "CreditUsage"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CreditUsage_workspaceId_createdAt_idx"
  ON "CreditUsage"("workspaceId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CreditUsage_userId_createdAt_idx"
  ON "CreditUsage"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CreditUsage_serviceType_idx" ON "CreditUsage"("serviceType");
CREATE INDEX IF NOT EXISTS "CreditUsage_provider_idx" ON "CreditUsage"("provider");

CREATE TABLE IF NOT EXISTS "UsageMetrics" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "userId" TEXT,
  "provider" TEXT,
  "period" TEXT NOT NULL,
  "periodKey" TEXT NOT NULL,
  "creditsUsed" INTEGER NOT NULL DEFAULT 0,
  "requestCount" INTEGER NOT NULL DEFAULT 0,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "UsageMetrics_organizationId_period_periodKey_idx"
  ON "UsageMetrics"("organizationId", "period", "periodKey");
CREATE INDEX IF NOT EXISTS "UsageMetrics_workspaceId_period_periodKey_idx"
  ON "UsageMetrics"("workspaceId", "period", "periodKey");
CREATE INDEX IF NOT EXISTS "UsageMetrics_userId_period_periodKey_idx"
  ON "UsageMetrics"("userId", "period", "periodKey");
CREATE INDEX IF NOT EXISTS "UsageMetrics_provider_period_periodKey_idx"
  ON "UsageMetrics"("provider", "period", "periodKey");

CREATE TABLE IF NOT EXISTS "UsageQuotas" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "teamId" TEXT,
  "planKey" TEXT NOT NULL DEFAULT 'free_trial',
  "dailyLimit" INTEGER NOT NULL DEFAULT 50,
  "monthlyLimit" INTEGER NOT NULL DEFAULT 100,
  "trialLimit" INTEGER NOT NULL DEFAULT 100,
  "unlimited" BOOLEAN NOT NULL DEFAULT false,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "UsageQuotas_organizationId_idx" ON "UsageQuotas"("organizationId");
CREATE INDEX IF NOT EXISTS "UsageQuotas_workspaceId_idx" ON "UsageQuotas"("workspaceId");
CREATE INDEX IF NOT EXISTS "UsageQuotas_teamId_idx" ON "UsageQuotas"("teamId");
CREATE INDEX IF NOT EXISTS "UsageQuotas_planKey_idx" ON "UsageQuotas"("planKey");

CREATE TABLE IF NOT EXISTS "AIUsageHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "userId" TEXT,
  "serviceType" TEXT NOT NULL,
  "provider" TEXT NOT NULL DEFAULT 'default',
  "credits" INTEGER NOT NULL,
  "costUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "detail" TEXT NOT NULL DEFAULT '',
  "usageEventId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AIUsageHistory_organizationId_createdAt_idx"
  ON "AIUsageHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AIUsageHistory_serviceType_idx" ON "AIUsageHistory"("serviceType");
CREATE INDEX IF NOT EXISTS "AIUsageHistory_provider_idx" ON "AIUsageHistory"("provider");

CREATE TABLE IF NOT EXISTS "CostCalculations" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "serviceType" TEXT NOT NULL,
  "provider" TEXT NOT NULL DEFAULT 'default',
  "credits" INTEGER NOT NULL,
  "quantity" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "providerCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "gpuCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "modelCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "retailValueUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "estimatedMarginUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "marginPct" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CostCalculations_organizationId_createdAt_idx"
  ON "CostCalculations"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CostCalculations_serviceType_idx" ON "CostCalculations"("serviceType");
CREATE INDEX IF NOT EXISTS "CostCalculations_provider_idx" ON "CostCalculations"("provider");

CREATE TABLE IF NOT EXISTS "ProviderCosts" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT,
  "provider" TEXT NOT NULL UNIQUE,
  "costPerCreditUsd" DOUBLE PRECISION NOT NULL,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProviderCosts_organizationId_idx" ON "ProviderCosts"("organizationId");
CREATE INDEX IF NOT EXISTS "ProviderCosts_active_idx" ON "ProviderCosts"("active");
