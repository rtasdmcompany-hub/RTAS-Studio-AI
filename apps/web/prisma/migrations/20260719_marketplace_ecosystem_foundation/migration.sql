-- Phase 9 Sprint 1 — AI Marketplace Ecosystem Foundation (UP)

CREATE TABLE IF NOT EXISTS "MarketplaceCreators" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "displayName" TEXT NOT NULL,
  "handle" TEXT NOT NULL,
  "creatorType" TEXT NOT NULL DEFAULT 'creator',
  "bio" TEXT NOT NULL DEFAULT '',
  "website" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'active',
  "publishedAssets" INTEGER NOT NULL DEFAULT 0,
  "totalVersions" INTEGER NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "MarketplaceCreators_handle_key" UNIQUE ("handle"),
  CONSTRAINT "MarketplaceCreators_organizationId_userId_key" UNIQUE ("organizationId", "userId")
);
CREATE INDEX IF NOT EXISTS "MarketplaceCreators_organizationId_idx" ON "MarketplaceCreators"("organizationId");
CREATE INDEX IF NOT EXISTS "MarketplaceCreators_status_idx" ON "MarketplaceCreators"("status");

CREATE TABLE IF NOT EXISTS "MarketplaceAssets" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "creatorId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "assetType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "category" TEXT NOT NULL DEFAULT 'other',
  "tagsJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "visibility" TEXT NOT NULL DEFAULT 'public',
  "currentVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "workspaceId" TEXT,
  "metadataJson" JSONB,
  "publishedAt" TIMESTAMP(3),
  "archivedAt" TIMESTAMP(3),
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "MarketplaceAssets_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "MarketplaceCreators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_organizationId_idx" ON "MarketplaceAssets"("organizationId");
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_creatorId_idx" ON "MarketplaceAssets"("creatorId");
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_ownerUserId_idx" ON "MarketplaceAssets"("ownerUserId");
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_status_idx" ON "MarketplaceAssets"("status");
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_assetType_idx" ON "MarketplaceAssets"("assetType");
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_category_idx" ON "MarketplaceAssets"("category");
CREATE INDEX IF NOT EXISTS "MarketplaceAssets_visibility_idx" ON "MarketplaceAssets"("visibility");

CREATE TABLE IF NOT EXISTS "AssetVersions" (
  "id" TEXT PRIMARY KEY,
  "assetId" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "changelog" TEXT NOT NULL DEFAULT '',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "createdBy" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AssetVersions_assetId_version_key" UNIQUE ("assetId", "version"),
  CONSTRAINT "AssetVersions_assetId_fkey" FOREIGN KEY ("assetId")
    REFERENCES "MarketplaceAssets"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AssetVersions_assetId_createdAt_idx"
  ON "AssetVersions"("assetId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "AssetCategories" (
  "id" TEXT PRIMARY KEY,
  "slug" TEXT NOT NULL,
  "label" TEXT NOT NULL DEFAULT '',
  "description" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AssetCategories_slug_key" UNIQUE ("slug")
);
CREATE INDEX IF NOT EXISTS "AssetCategories_active_idx" ON "AssetCategories"("active");

CREATE TABLE IF NOT EXISTS "AssetTags" (
  "id" TEXT PRIMARY KEY,
  "slug" TEXT NOT NULL,
  "usageCount" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AssetTags_slug_key" UNIQUE ("slug")
);
CREATE INDEX IF NOT EXISTS "AssetTags_usageCount_idx" ON "AssetTags"("usageCount");

CREATE TABLE IF NOT EXISTS "AssetCollections" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "creatorId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "assetIdsJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AssetCollections_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "MarketplaceCreators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AssetCollections_organizationId_idx" ON "AssetCollections"("organizationId");
CREATE INDEX IF NOT EXISTS "AssetCollections_creatorId_idx" ON "AssetCollections"("creatorId");

-- Seed the default asset category taxonomy
INSERT INTO "AssetCategories" ("id", "slug", "label") VALUES
  (gen_random_uuid()::text, 'ai_templates', 'AI Templates'),
  (gen_random_uuid()::text, 'prompts', 'Prompt Packs'),
  (gen_random_uuid()::text, 'characters', 'Characters'),
  (gen_random_uuid()::text, 'voice', 'Voice Models'),
  (gen_random_uuid()::text, 'music', 'Music Packs'),
  (gen_random_uuid()::text, 'video', 'Video Templates'),
  (gen_random_uuid()::text, 'image', 'Image Templates'),
  (gen_random_uuid()::text, 'workflows', 'Workflow Templates'),
  (gen_random_uuid()::text, 'automation', 'Automation Packs'),
  (gen_random_uuid()::text, 'other', 'Other')
ON CONFLICT ("slug") DO NOTHING;
