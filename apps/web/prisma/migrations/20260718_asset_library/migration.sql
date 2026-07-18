-- Phase 7 Sprint 5 — Enterprise Asset Management & Digital Library Engine (UP)

CREATE TABLE IF NOT EXISTS "LibraryAsset" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ownerId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "assetType" TEXT NOT NULL,
  "mimeType" TEXT,
  "category" TEXT NOT NULL DEFAULT 'general',
  "status" TEXT NOT NULL DEFAULT 'active',
  "storageKey" TEXT NOT NULL,
  "storageUrl" TEXT,
  "sizeBytes" INTEGER NOT NULL DEFAULT 0,
  "checksum" TEXT,
  "currentVersion" INTEGER NOT NULL DEFAULT 1,
  "isFavorite" BOOLEAN NOT NULL DEFAULT false,
  "isShared" BOOLEAN NOT NULL DEFAULT false,
  "downloadCount" INTEGER NOT NULL DEFAULT 0,
  "useCount" INTEGER NOT NULL DEFAULT 0,
  "tagsJson" JSONB,
  "metadataJson" JSONB,
  "previewUrl" TEXT,
  "archivedAt" TIMESTAMP(3),
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "LibraryAsset_organizationId_slug_key" UNIQUE ("organizationId", "slug")
);
CREATE INDEX IF NOT EXISTS "LibraryAsset_organizationId_assetType_createdAt_idx"
  ON "LibraryAsset"("organizationId", "assetType", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "LibraryAsset_workspaceId_status_idx" ON "LibraryAsset"("workspaceId", "status");
CREATE INDEX IF NOT EXISTS "LibraryAsset_ownerId_idx" ON "LibraryAsset"("ownerId");
CREATE INDEX IF NOT EXISTS "LibraryAsset_category_idx" ON "LibraryAsset"("category");
CREATE INDEX IF NOT EXISTS "LibraryAsset_status_idx" ON "LibraryAsset"("status");
CREATE INDEX IF NOT EXISTS "LibraryAsset_isFavorite_idx" ON "LibraryAsset"("isFavorite");
CREATE INDEX IF NOT EXISTS "LibraryAsset_deletedAt_idx" ON "LibraryAsset"("deletedAt");

CREATE TABLE IF NOT EXISTS "LibraryAssetVersion" (
  "id" TEXT PRIMARY KEY,
  "assetId" TEXT NOT NULL,
  "version" INTEGER NOT NULL,
  "storageKey" TEXT NOT NULL,
  "storageUrl" TEXT,
  "sizeBytes" INTEGER NOT NULL DEFAULT 0,
  "checksum" TEXT,
  "note" TEXT,
  "createdById" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "LibraryAssetVersion_assetId_version_key" UNIQUE ("assetId", "version")
);
CREATE INDEX IF NOT EXISTS "LibraryAssetVersion_assetId_createdAt_idx"
  ON "LibraryAssetVersion"("assetId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "LibraryAssetMetadata" (
  "id" TEXT PRIMARY KEY,
  "assetId" TEXT NOT NULL UNIQUE,
  "title" TEXT,
  "description" TEXT,
  "width" INTEGER,
  "height" INTEGER,
  "durationSec" DOUBLE PRECISION,
  "language" TEXT,
  "attributesJson" JSONB,
  "embeddingHint" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "LibraryAssetTag" (
  "id" TEXT PRIMARY KEY,
  "assetId" TEXT NOT NULL,
  "tag" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "LibraryAssetTag_assetId_tag_key" UNIQUE ("assetId", "tag")
);
CREATE INDEX IF NOT EXISTS "LibraryAssetTag_tag_idx" ON "LibraryAssetTag"("tag");

CREATE TABLE IF NOT EXISTS "LibraryAssetCategory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT,
  "key" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "isSystem" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS "LibraryAssetCategory_organizationId_key_key"
  ON "LibraryAssetCategory"("organizationId", "key");
CREATE INDEX IF NOT EXISTS "LibraryAssetCategory_key_idx" ON "LibraryAssetCategory"("key");

CREATE TABLE IF NOT EXISTS "LibraryAssetPermission" (
  "id" TEXT PRIMARY KEY,
  "assetId" TEXT NOT NULL,
  "subjectType" TEXT NOT NULL,
  "subjectId" TEXT NOT NULL,
  "role" TEXT NOT NULL DEFAULT 'read',
  "userId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "LibraryAssetPermission_assetId_subjectType_subjectId_key"
    UNIQUE ("assetId", "subjectType", "subjectId")
);
CREATE INDEX IF NOT EXISTS "LibraryAssetPermission_subjectType_subjectId_idx"
  ON "LibraryAssetPermission"("subjectType", "subjectId");
CREATE INDEX IF NOT EXISTS "LibraryAssetPermission_userId_idx" ON "LibraryAssetPermission"("userId");

CREATE TABLE IF NOT EXISTS "LibraryAssetActivity" (
  "id" TEXT PRIMARY KEY,
  "assetId" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "detail" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LibraryAssetActivity_assetId_createdAt_idx"
  ON "LibraryAssetActivity"("assetId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "LibraryAssetActivity_actorId_idx" ON "LibraryAssetActivity"("actorId");
CREATE INDEX IF NOT EXISTS "LibraryAssetActivity_action_idx" ON "LibraryAssetActivity"("action");

CREATE TABLE IF NOT EXISTS "LibraryAssetCollection" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "libraryScope" TEXT NOT NULL DEFAULT 'organization',
  "description" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "LibraryAssetCollection_organizationId_slug_key" UNIQUE ("organizationId", "slug")
);
CREATE INDEX IF NOT EXISTS "LibraryAssetCollection_workspaceId_idx" ON "LibraryAssetCollection"("workspaceId");
CREATE INDEX IF NOT EXISTS "LibraryAssetCollection_libraryScope_idx" ON "LibraryAssetCollection"("libraryScope");

CREATE TABLE IF NOT EXISTS "LibraryAssetCollectionItem" (
  "id" TEXT PRIMARY KEY,
  "collectionId" TEXT NOT NULL,
  "assetId" TEXT NOT NULL,
  "position" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "LibraryAssetCollectionItem_collectionId_assetId_key" UNIQUE ("collectionId", "assetId")
);
CREATE INDEX IF NOT EXISTS "LibraryAssetCollectionItem_assetId_idx" ON "LibraryAssetCollectionItem"("assetId");
