-- Phase 9 Sprint 4 — Template Store, Versioning & Asset Management (UP)
-- AssetCategories, AssetTags and AssetCollections tables already exist
-- (created in the Phase 9 Sprint 1 marketplace ecosystem migration).

CREATE TABLE IF NOT EXISTS "AssetLibraries" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AssetLibraries_organizationId_idx" ON "AssetLibraries"("organizationId");
CREATE INDEX IF NOT EXISTS "AssetLibraries_ownerUserId_idx" ON "AssetLibraries"("ownerUserId");

CREATE TABLE IF NOT EXISTS "Templates" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "templateType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "category" TEXT NOT NULL DEFAULT 'other',
  "tagsJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'active',
  "featured" BOOLEAN NOT NULL DEFAULT FALSE,
  "currentVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "libraryId" TEXT,
  "downloads" INTEGER NOT NULL DEFAULT 0,
  "ratingTotal" INTEGER NOT NULL DEFAULT 0,
  "ratingCount" INTEGER NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "archivedAt" TIMESTAMP(3),
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Templates_libraryId_fkey" FOREIGN KEY ("libraryId")
    REFERENCES "AssetLibraries"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "Templates_organizationId_idx" ON "Templates"("organizationId");
CREATE INDEX IF NOT EXISTS "Templates_ownerUserId_idx" ON "Templates"("ownerUserId");
CREATE INDEX IF NOT EXISTS "Templates_status_idx" ON "Templates"("status");
CREATE INDEX IF NOT EXISTS "Templates_templateType_idx" ON "Templates"("templateType");
CREATE INDEX IF NOT EXISTS "Templates_category_idx" ON "Templates"("category");
CREATE INDEX IF NOT EXISTS "Templates_featured_idx" ON "Templates"("featured");
CREATE INDEX IF NOT EXISTS "Templates_libraryId_idx" ON "Templates"("libraryId");

CREATE TABLE IF NOT EXISTS "TemplateVersions" (
  "id" TEXT PRIMARY KEY,
  "templateId" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "changelog" TEXT NOT NULL DEFAULT '',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "checksum" TEXT NOT NULL DEFAULT '',
  "createdBy" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "TemplateVersions_templateId_version_key" UNIQUE ("templateId", "version"),
  CONSTRAINT "TemplateVersions_templateId_fkey" FOREIGN KEY ("templateId")
    REFERENCES "Templates"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "TemplateVersions_templateId_createdAt_idx"
  ON "TemplateVersions"("templateId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "AssetSearchIndex" (
  "id" TEXT PRIMARY KEY,
  "templateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "tokensJson" JSONB,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AssetSearchIndex_templateId_key" UNIQUE ("templateId"),
  CONSTRAINT "AssetSearchIndex_templateId_fkey" FOREIGN KEY ("templateId")
    REFERENCES "Templates"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AssetSearchIndex_organizationId_idx" ON "AssetSearchIndex"("organizationId");
