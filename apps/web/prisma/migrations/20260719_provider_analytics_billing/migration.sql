-- Phase 8 Sprint 8 — Usage Analytics, Cost Optimization & AI Provider Billing (UP)

CREATE TABLE IF NOT EXISTS "ProviderUsage" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "provider" TEXT NOT NULL,
  "model" TEXT NOT NULL DEFAULT '',
  "userId" TEXT,
  "workspaceId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'success',
  "latencyMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "creditsCharged" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "costBreakdownJson" JSONB,
  "totalCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "revenueUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProviderUsage_organizationId_createdAt_idx"
  ON "ProviderUsage"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ProviderUsage_provider_idx" ON "ProviderUsage"("provider");
CREATE INDEX IF NOT EXISTS "ProviderUsage_userId_idx" ON "ProviderUsage"("userId");
CREATE INDEX IF NOT EXISTS "ProviderUsage_workspaceId_idx" ON "ProviderUsage"("workspaceId");
CREATE INDEX IF NOT EXISTS "ProviderUsage_status_idx" ON "ProviderUsage"("status");

CREATE TABLE IF NOT EXISTS "UsageAnalytics" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "period" TEXT NOT NULL,
  "dimension" TEXT NOT NULL DEFAULT 'provider',
  "dimensionValue" TEXT NOT NULL DEFAULT '',
  "requests" INTEGER NOT NULL DEFAULT 0,
  "successful" INTEGER NOT NULL DEFAULT 0,
  "failed" INTEGER NOT NULL DEFAULT 0,
  "costUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "revenueUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "UsageAnalytics_org_period_dim_key"
    UNIQUE ("organizationId", "period", "dimension", "dimensionValue")
);
CREATE INDEX IF NOT EXISTS "UsageAnalytics_organizationId_period_idx"
  ON "UsageAnalytics"("organizationId", "period");
CREATE INDEX IF NOT EXISTS "UsageAnalytics_dimension_idx" ON "UsageAnalytics"("dimension");

CREATE TABLE IF NOT EXISTS "CostAnalytics" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "period" TEXT NOT NULL,
  "providerCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "gpuCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "apiCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "storageCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "bandwidthCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "renderingCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "totalCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "costPerGenerationUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "monthlyOperatingCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CostAnalytics_org_period_key" UNIQUE ("organizationId", "period")
);
CREATE INDEX IF NOT EXISTS "CostAnalytics_organizationId_idx" ON "CostAnalytics"("organizationId");

CREATE TABLE IF NOT EXISTS "BudgetPolicies" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "scope" TEXT NOT NULL DEFAULT 'organization',
  "scopeId" TEXT NOT NULL,
  "dailyLimitUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "monthlyLimitUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "alertsEnabled" BOOLEAN NOT NULL DEFAULT true,
  "hardStop" BOOLEAN NOT NULL DEFAULT false,
  "updatedBy" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "BudgetPolicies_scope_scopeId_key" UNIQUE ("scope", "scopeId")
);
CREATE INDEX IF NOT EXISTS "BudgetPolicies_organizationId_idx" ON "BudgetPolicies"("organizationId");

CREATE TABLE IF NOT EXISTS "BudgetEvents" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "policyId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "period" TEXT NOT NULL DEFAULT 'daily',
  "thresholdPct" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "spentUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "limitUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "detail" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "BudgetEvents_organizationId_createdAt_idx"
  ON "BudgetEvents"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "BudgetEvents_policyId_idx" ON "BudgetEvents"("policyId");
CREATE INDEX IF NOT EXISTS "BudgetEvents_eventType_idx" ON "BudgetEvents"("eventType");

CREATE TABLE IF NOT EXISTS "ProfitReports" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "period" TEXT NOT NULL,
  "revenueUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "providerCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "infrastructureCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "fixedOverheadUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "grossProfitUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "netProfitUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "marginPct" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "generatedBy" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProfitReports_organizationId_createdAt_idx"
  ON "ProfitReports"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ProfitReports_period_idx" ON "ProfitReports"("period");

CREATE TABLE IF NOT EXISTS "CostOptimizationHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "mode" TEXT NOT NULL,
  "capability" TEXT NOT NULL DEFAULT '',
  "selectedProvider" TEXT NOT NULL,
  "estimatedCostUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "estimatedLatencyMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "qualityScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "savingsUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "reason" TEXT NOT NULL DEFAULT '',
  "rankingJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CostOptimizationHistory_organizationId_createdAt_idx"
  ON "CostOptimizationHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CostOptimizationHistory_selectedProvider_idx"
  ON "CostOptimizationHistory"("selectedProvider");
CREATE INDEX IF NOT EXISTS "CostOptimizationHistory_mode_idx" ON "CostOptimizationHistory"("mode");
