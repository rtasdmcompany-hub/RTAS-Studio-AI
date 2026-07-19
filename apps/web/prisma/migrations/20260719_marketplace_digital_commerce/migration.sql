-- Phase 8 Sprint 9 — Marketplace, Template Store & Digital Commerce (UP)

CREATE TABLE IF NOT EXISTS "MarketplaceProducts" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "sellerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "productType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "category" TEXT NOT NULL DEFAULT 'other',
  "tagsJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "pricingModel" TEXT NOT NULL DEFAULT 'free',
  "priceCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "licenseType" TEXT NOT NULL DEFAULT 'personal',
  "featured" BOOLEAN NOT NULL DEFAULT false,
  "workspaceId" TEXT,
  "currentVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "views" INTEGER NOT NULL DEFAULT 0,
  "downloads" INTEGER NOT NULL DEFAULT 0,
  "purchases" INTEGER NOT NULL DEFAULT 0,
  "refunds" INTEGER NOT NULL DEFAULT 0,
  "revenueCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "ratingSum" INTEGER NOT NULL DEFAULT 0,
  "ratingCount" INTEGER NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "publishedAt" TIMESTAMP(3),
  "archivedAt" TIMESTAMP(3),
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MarketplaceProducts_organizationId_idx" ON "MarketplaceProducts"("organizationId");
CREATE INDEX IF NOT EXISTS "MarketplaceProducts_sellerUserId_idx" ON "MarketplaceProducts"("sellerUserId");
CREATE INDEX IF NOT EXISTS "MarketplaceProducts_status_idx" ON "MarketplaceProducts"("status");
CREATE INDEX IF NOT EXISTS "MarketplaceProducts_category_idx" ON "MarketplaceProducts"("category");
CREATE INDEX IF NOT EXISTS "MarketplaceProducts_productType_idx" ON "MarketplaceProducts"("productType");
CREATE INDEX IF NOT EXISTS "MarketplaceProducts_featured_idx" ON "MarketplaceProducts"("featured");

CREATE TABLE IF NOT EXISTS "ProductVersions" (
  "id" TEXT PRIMARY KEY,
  "productId" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "changelog" TEXT NOT NULL DEFAULT '',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ProductVersions_productId_version_key" UNIQUE ("productId", "version")
);
CREATE INDEX IF NOT EXISTS "ProductVersions_productId_createdAt_idx"
  ON "ProductVersions"("productId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "Purchases" (
  "id" TEXT PRIMARY KEY,
  "productId" TEXT NOT NULL,
  "productName" TEXT NOT NULL DEFAULT '',
  "buyerUserId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "priceCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'completed',
  "licenseId" TEXT,
  "refundedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Purchases_productId_idx" ON "Purchases"("productId");
CREATE INDEX IF NOT EXISTS "Purchases_buyerUserId_idx" ON "Purchases"("buyerUserId");
CREATE INDEX IF NOT EXISTS "Purchases_organizationId_createdAt_idx"
  ON "Purchases"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Purchases_status_idx" ON "Purchases"("status");

CREATE TABLE IF NOT EXISTS "ProductLicenses" (
  "id" TEXT PRIMARY KEY,
  "productId" TEXT NOT NULL,
  "purchaseId" TEXT NOT NULL DEFAULT '',
  "organizationId" TEXT NOT NULL,
  "holderUserId" TEXT NOT NULL,
  "licenseKey" TEXT NOT NULL UNIQUE,
  "licenseType" TEXT NOT NULL DEFAULT 'personal',
  "status" TEXT NOT NULL DEFAULT 'active',
  "workspaceId" TEXT,
  "revokedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProductLicenses_productId_idx" ON "ProductLicenses"("productId");
CREATE INDEX IF NOT EXISTS "ProductLicenses_holderUserId_idx" ON "ProductLicenses"("holderUserId");
CREATE INDEX IF NOT EXISTS "ProductLicenses_organizationId_idx" ON "ProductLicenses"("organizationId");
CREATE INDEX IF NOT EXISTS "ProductLicenses_status_idx" ON "ProductLicenses"("status");

CREATE TABLE IF NOT EXISTS "ProductReviews" (
  "id" TEXT PRIMARY KEY,
  "productId" TEXT NOT NULL,
  "reviewerUserId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "rating" INTEGER NOT NULL,
  "title" TEXT NOT NULL DEFAULT '',
  "body" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ProductReviews_productId_reviewerUserId_key" UNIQUE ("productId", "reviewerUserId")
);
CREATE INDEX IF NOT EXISTS "ProductReviews_productId_createdAt_idx"
  ON "ProductReviews"("productId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ProductReviews_organizationId_idx" ON "ProductReviews"("organizationId");
CREATE INDEX IF NOT EXISTS "ProductReviews_rating_idx" ON "ProductReviews"("rating");

CREATE TABLE IF NOT EXISTS "MarketplaceAnalytics" (
  "id" TEXT PRIMARY KEY,
  "productId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "userId" TEXT,
  "organizationId" TEXT,
  "amountCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MarketplaceAnalytics_productId_createdAt_idx"
  ON "MarketplaceAnalytics"("productId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "MarketplaceAnalytics_eventType_idx" ON "MarketplaceAnalytics"("eventType");
CREATE INDEX IF NOT EXISTS "MarketplaceAnalytics_organizationId_idx" ON "MarketplaceAnalytics"("organizationId");

CREATE TABLE IF NOT EXISTS "ProductCategories" (
  "id" TEXT PRIMARY KEY,
  "slug" TEXT NOT NULL UNIQUE,
  "label" TEXT NOT NULL DEFAULT '',
  "description" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProductCategories_active_idx" ON "ProductCategories"("active");

CREATE TABLE IF NOT EXISTS "ProductTags" (
  "id" TEXT PRIMARY KEY,
  "slug" TEXT NOT NULL UNIQUE,
  "usageCount" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProductTags_usageCount_idx" ON "ProductTags"("usageCount");

CREATE TABLE IF NOT EXISTS "ProductRatings" (
  "id" TEXT PRIMARY KEY,
  "productId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "rating" INTEGER NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ProductRatings_productId_userId_key" UNIQUE ("productId", "userId")
);
CREATE INDEX IF NOT EXISTS "ProductRatings_productId_idx" ON "ProductRatings"("productId");
CREATE INDEX IF NOT EXISTS "ProductRatings_rating_idx" ON "ProductRatings"("rating");

-- Seed default categories
INSERT INTO "ProductCategories" ("id", "slug", "label") VALUES
  (gen_random_uuid(), 'templates', 'Templates'),
  (gen_random_uuid(), 'workflows', 'AI Workflows'),
  (gen_random_uuid(), 'characters', 'Characters'),
  (gen_random_uuid(), 'audio', 'Audio'),
  (gen_random_uuid(), 'video', 'Video'),
  (gen_random_uuid(), 'branding', 'Branding'),
  (gen_random_uuid(), 'effects', 'Effects'),
  (gen_random_uuid(), 'other', 'Other')
ON CONFLICT ("slug") DO NOTHING;
