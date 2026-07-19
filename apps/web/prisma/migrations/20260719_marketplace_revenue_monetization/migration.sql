-- Phase 9 Sprint 9 — Marketplace Analytics, Revenue Intelligence & Monetization (UP)

CREATE TABLE IF NOT EXISTS "RevenueReports" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "period" TEXT NOT NULL,
  "grossRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "netRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "refundAmount" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "subscriptionRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "marketplaceRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "creditSalesRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RevenueReports_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "RevenueReports_organizationId_period_idx"
  ON "RevenueReports"("organizationId", "period");
CREATE INDEX IF NOT EXISTS "RevenueReports_workspaceId_idx" ON "RevenueReports"("workspaceId");

CREATE TABLE IF NOT EXISTS "SalesReports" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "period" TEXT NOT NULL DEFAULT '',
  "totalSales" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "salesCount" INTEGER NOT NULL DEFAULT 0,
  "refundCount" INTEGER NOT NULL DEFAULT 0,
  "salesGrowth" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "byEventTypeJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "SalesReports_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "SalesReports_organizationId_createdAt_idx"
  ON "SalesReports"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "SalesReports_workspaceId_idx" ON "SalesReports"("workspaceId");

-- Aggregate marketplace analytics (event-level MarketplaceAnalytics already exists)
CREATE TABLE IF NOT EXISTS "RevenueMarketplaceAnalytics" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "period" TEXT NOT NULL DEFAULT '',
  "productViews" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "productDownloads" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "productPurchases" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "conversionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "healthScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "bestSellersJson" JSONB,
  "trendingJson" JSONB,
  "categoryJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RevenueMarketplaceAnalytics_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "RevenueMarketplaceAnalytics_organizationId_period_idx"
  ON "RevenueMarketplaceAnalytics"("organizationId", "period");

CREATE TABLE IF NOT EXISTS "CreatorRevenue" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "creatorId" TEXT NOT NULL,
  "revenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "sales" INTEGER NOT NULL DEFAULT 0,
  "downloads" INTEGER NOT NULL DEFAULT 0,
  "views" INTEGER NOT NULL DEFAULT 0,
  "averageRating" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "reviewCount" INTEGER NOT NULL DEFAULT 0,
  "conversionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "revenueGrowth" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CreatorRevenue_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "CreatorRevenue_organizationId_creatorId_key"
  ON "CreatorRevenue"("organizationId", "creatorId");
CREATE INDEX IF NOT EXISTS "CreatorRevenue_organizationId_idx" ON "CreatorRevenue"("organizationId");
CREATE INDEX IF NOT EXISTS "CreatorRevenue_creatorId_idx" ON "CreatorRevenue"("creatorId");

CREATE TABLE IF NOT EXISTS "RevenueForecasts" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "horizon" TEXT NOT NULL,
  "baseline" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "growthRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "projectedJson" JSONB,
  "salesForecastJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RevenueForecasts_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "RevenueForecasts_organizationId_horizon_idx"
  ON "RevenueForecasts"("organizationId", "horizon");

CREATE TABLE IF NOT EXISTS "CustomerMetrics" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "customerId" TEXT NOT NULL,
  "totalSpend" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "purchases" INTEGER NOT NULL DEFAULT 0,
  "churned" BOOLEAN NOT NULL DEFAULT FALSE,
  "firstSeenAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "lastSeenAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "lifetimeValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CustomerMetrics_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "CustomerMetrics_organizationId_customerId_key"
  ON "CustomerMetrics"("organizationId", "customerId");
CREATE INDEX IF NOT EXISTS "CustomerMetrics_organizationId_idx" ON "CustomerMetrics"("organizationId");
CREATE INDEX IF NOT EXISTS "CustomerMetrics_churned_idx" ON "CustomerMetrics"("churned");

CREATE TABLE IF NOT EXISTS "ProductPerformance" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "productId" TEXT NOT NULL,
  "category" TEXT NOT NULL DEFAULT 'other',
  "views" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "downloads" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "purchases" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "revenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "featured" BOOLEAN NOT NULL DEFAULT FALSE,
  "searchImpressions" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ProductPerformance_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "ProductPerformance_organizationId_productId_key"
  ON "ProductPerformance"("organizationId", "productId");
CREATE INDEX IF NOT EXISTS "ProductPerformance_organizationId_idx" ON "ProductPerformance"("organizationId");
CREATE INDEX IF NOT EXISTS "ProductPerformance_category_idx" ON "ProductPerformance"("category");

CREATE TABLE IF NOT EXISTS "FinancialSummaries" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "period" TEXT NOT NULL,
  "grossRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "refundAmount" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "netRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "subscriptionRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "marketplaceRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "creditSalesRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "FinancialSummaries_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "FinancialSummaries_organizationId_period_idx"
  ON "FinancialSummaries"("organizationId", "period");
