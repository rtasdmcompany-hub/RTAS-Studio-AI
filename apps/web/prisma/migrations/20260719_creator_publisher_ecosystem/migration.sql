-- Phase 9 Sprint 2 — Creator Platform & Publisher Ecosystem (UP)

CREATE TABLE IF NOT EXISTS "Creators" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "displayName" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'active',
  "verificationStatus" TEXT NOT NULL DEFAULT 'unverified',
  "verifiedAt" TIMESTAMP(3),
  "verificationNote" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Creators_organizationId_userId_key" UNIQUE ("organizationId", "userId")
);
CREATE INDEX IF NOT EXISTS "Creators_organizationId_idx" ON "Creators"("organizationId");
CREATE INDEX IF NOT EXISTS "Creators_verificationStatus_idx" ON "Creators"("verificationStatus");
CREATE INDEX IF NOT EXISTS "Creators_status_idx" ON "Creators"("status");

CREATE TABLE IF NOT EXISTS "CreatorProfiles" (
  "id" TEXT PRIMARY KEY,
  "creatorId" TEXT NOT NULL,
  "bio" TEXT NOT NULL DEFAULT '',
  "avatarUri" TEXT NOT NULL DEFAULT '',
  "socialLinksJson" JSONB,
  "categoriesJson" JSONB,
  "portfolioJson" JSONB,
  "featuredIdsJson" JSONB,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CreatorProfiles_creatorId_key" UNIQUE ("creatorId"),
  CONSTRAINT "CreatorProfiles_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "Creators"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "CreatorBadges" (
  "id" TEXT PRIMARY KEY,
  "creatorId" TEXT NOT NULL,
  "badgeKey" TEXT NOT NULL,
  "label" TEXT NOT NULL DEFAULT '',
  "description" TEXT NOT NULL DEFAULT '',
  "awardedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CreatorBadges_creatorId_badgeKey_key" UNIQUE ("creatorId", "badgeKey"),
  CONSTRAINT "CreatorBadges_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "Creators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "CreatorBadges_creatorId_idx" ON "CreatorBadges"("creatorId");
CREATE INDEX IF NOT EXISTS "CreatorBadges_badgeKey_idx" ON "CreatorBadges"("badgeKey");

CREATE TABLE IF NOT EXISTS "CreatorFollowers" (
  "id" TEXT PRIMARY KEY,
  "creatorId" TEXT NOT NULL,
  "followerUserId" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CreatorFollowers_creatorId_followerUserId_key" UNIQUE ("creatorId", "followerUserId"),
  CONSTRAINT "CreatorFollowers_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "Creators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "CreatorFollowers_creatorId_idx" ON "CreatorFollowers"("creatorId");
CREATE INDEX IF NOT EXISTS "CreatorFollowers_followerUserId_idx" ON "CreatorFollowers"("followerUserId");

CREATE TABLE IF NOT EXISTS "PublishedAssets" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "creatorId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "assetType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "category" TEXT NOT NULL DEFAULT 'other',
  "tagsJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'published',
  "visibility" TEXT NOT NULL DEFAULT 'public',
  "currentVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "versionsJson" JSONB,
  "assetUri" TEXT NOT NULL DEFAULT '',
  "priceCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "publishAt" TIMESTAMP(3),
  "publishedAt" TIMESTAMP(3),
  "archivedAt" TIMESTAMP(3),
  "deletedAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PublishedAssets_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "Creators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "PublishedAssets_organizationId_idx" ON "PublishedAssets"("organizationId");
CREATE INDEX IF NOT EXISTS "PublishedAssets_creatorId_idx" ON "PublishedAssets"("creatorId");
CREATE INDEX IF NOT EXISTS "PublishedAssets_ownerUserId_idx" ON "PublishedAssets"("ownerUserId");
CREATE INDEX IF NOT EXISTS "PublishedAssets_status_idx" ON "PublishedAssets"("status");
CREATE INDEX IF NOT EXISTS "PublishedAssets_assetType_idx" ON "PublishedAssets"("assetType");
CREATE INDEX IF NOT EXISTS "PublishedAssets_visibility_idx" ON "PublishedAssets"("visibility");

CREATE TABLE IF NOT EXISTS "AssetDrafts" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "creatorId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "assetType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "category" TEXT NOT NULL DEFAULT 'other',
  "tagsJson" JSONB,
  "visibility" TEXT NOT NULL DEFAULT 'public',
  "assetUri" TEXT NOT NULL DEFAULT '',
  "priceCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "publishAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AssetDrafts_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "Creators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AssetDrafts_organizationId_idx" ON "AssetDrafts"("organizationId");
CREATE INDEX IF NOT EXISTS "AssetDrafts_creatorId_idx" ON "AssetDrafts"("creatorId");
CREATE INDEX IF NOT EXISTS "AssetDrafts_ownerUserId_idx" ON "AssetDrafts"("ownerUserId");
CREATE INDEX IF NOT EXISTS "AssetDrafts_publishAt_idx" ON "AssetDrafts"("publishAt");

CREATE TABLE IF NOT EXISTS "CreatorAnalytics" (
  "id" TEXT PRIMARY KEY,
  "creatorId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "totalAssets" INTEGER NOT NULL DEFAULT 0,
  "publishedAssets" INTEGER NOT NULL DEFAULT 0,
  "views" INTEGER NOT NULL DEFAULT 0,
  "downloads" INTEGER NOT NULL DEFAULT 0,
  "purchases" INTEGER NOT NULL DEFAULT 0,
  "revenueCredits" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "followers" INTEGER NOT NULL DEFAULT 0,
  "avgRating" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "ratings" INTEGER NOT NULL DEFAULT 0,
  "reviews" INTEGER NOT NULL DEFAULT 0,
  "engagementScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "reputation" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "capturedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CreatorAnalytics_creatorId_fkey" FOREIGN KEY ("creatorId")
    REFERENCES "Creators"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "CreatorAnalytics_creatorId_capturedAt_idx"
  ON "CreatorAnalytics"("creatorId", "capturedAt" DESC);
CREATE INDEX IF NOT EXISTS "CreatorAnalytics_organizationId_idx" ON "CreatorAnalytics"("organizationId");
