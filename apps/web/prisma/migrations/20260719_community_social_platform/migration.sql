-- Phase 9 Sprint 3 — Community Platform & Social Collaboration Engine (UP)

CREATE TABLE IF NOT EXISTS "UserProfiles" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "displayName" TEXT NOT NULL,
  "handle" TEXT NOT NULL,
  "bio" TEXT NOT NULL DEFAULT '',
  "avatarUri" TEXT NOT NULL DEFAULT '',
  "verified" BOOLEAN NOT NULL DEFAULT FALSE,
  "verifiedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "UserProfiles_organizationId_userId_key" UNIQUE ("organizationId", "userId"),
  CONSTRAINT "UserProfiles_organizationId_handle_key" UNIQUE ("organizationId", "handle")
);
CREATE INDEX IF NOT EXISTS "UserProfiles_organizationId_idx" ON "UserProfiles"("organizationId");
CREATE INDEX IF NOT EXISTS "UserProfiles_verified_idx" ON "UserProfiles"("verified");

CREATE TABLE IF NOT EXISTS "Followers" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "followerUserId" TEXT NOT NULL,
  "targetUserId" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Followers_org_follower_target_key" UNIQUE ("organizationId", "followerUserId", "targetUserId")
);
CREATE INDEX IF NOT EXISTS "Followers_organizationId_targetUserId_idx" ON "Followers"("organizationId", "targetUserId");
CREATE INDEX IF NOT EXISTS "Followers_followerUserId_idx" ON "Followers"("followerUserId");

CREATE TABLE IF NOT EXISTS "Following" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "followerUserId" TEXT NOT NULL,
  "targetUserId" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Following_org_follower_target_key" UNIQUE ("organizationId", "followerUserId", "targetUserId")
);
CREATE INDEX IF NOT EXISTS "Following_organizationId_followerUserId_idx" ON "Following"("organizationId", "followerUserId");
CREATE INDEX IF NOT EXISTS "Following_targetUserId_idx" ON "Following"("targetUserId");

CREATE TABLE IF NOT EXISTS "Reviews" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "assetId" TEXT NOT NULL,
  "authorUserId" TEXT NOT NULL,
  "rating" INTEGER NOT NULL,
  "title" TEXT NOT NULL DEFAULT '',
  "body" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'visible',
  "assetCategory" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Reviews_org_asset_author_key" UNIQUE ("organizationId", "assetId", "authorUserId")
);
CREATE INDEX IF NOT EXISTS "Reviews_organizationId_idx" ON "Reviews"("organizationId");
CREATE INDEX IF NOT EXISTS "Reviews_assetId_idx" ON "Reviews"("assetId");
CREATE INDEX IF NOT EXISTS "Reviews_authorUserId_idx" ON "Reviews"("authorUserId");
CREATE INDEX IF NOT EXISTS "Reviews_status_idx" ON "Reviews"("status");

CREATE TABLE IF NOT EXISTS "Ratings" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "assetId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "value" INTEGER NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Ratings_org_asset_user_key" UNIQUE ("organizationId", "assetId", "userId")
);
CREATE INDEX IF NOT EXISTS "Ratings_organizationId_idx" ON "Ratings"("organizationId");
CREATE INDEX IF NOT EXISTS "Ratings_assetId_idx" ON "Ratings"("assetId");

CREATE TABLE IF NOT EXISTS "Comments" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "subjectId" TEXT NOT NULL,
  "authorUserId" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "parentId" TEXT,
  "mentionsJson" JSONB,
  "status" TEXT NOT NULL DEFAULT 'visible',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Comments_organizationId_idx" ON "Comments"("organizationId");
CREATE INDEX IF NOT EXISTS "Comments_subjectId_idx" ON "Comments"("subjectId");
CREATE INDEX IF NOT EXISTS "Comments_authorUserId_idx" ON "Comments"("authorUserId");
CREATE INDEX IF NOT EXISTS "Comments_parentId_idx" ON "Comments"("parentId");
CREATE INDEX IF NOT EXISTS "Comments_status_idx" ON "Comments"("status");

CREATE TABLE IF NOT EXISTS "Likes" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "assetId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "assetCategory" TEXT NOT NULL DEFAULT '',
  "assetOwnerUserId" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Likes_org_asset_user_key" UNIQUE ("organizationId", "assetId", "userId")
);
CREATE INDEX IF NOT EXISTS "Likes_organizationId_idx" ON "Likes"("organizationId");
CREATE INDEX IF NOT EXISTS "Likes_assetId_idx" ON "Likes"("assetId");
CREATE INDEX IF NOT EXISTS "Likes_assetOwnerUserId_idx" ON "Likes"("assetOwnerUserId");

CREATE TABLE IF NOT EXISTS "Favorites" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "assetId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "kind" TEXT NOT NULL DEFAULT 'favorite',
  "assetCategory" TEXT NOT NULL DEFAULT '',
  "assetOwnerUserId" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Favorites_org_asset_user_kind_key" UNIQUE ("organizationId", "assetId", "userId", "kind")
);
CREATE INDEX IF NOT EXISTS "Favorites_organizationId_idx" ON "Favorites"("organizationId");
CREATE INDEX IF NOT EXISTS "Favorites_userId_kind_idx" ON "Favorites"("userId", "kind");
CREATE INDEX IF NOT EXISTS "Favorites_assetId_idx" ON "Favorites"("assetId");

CREATE TABLE IF NOT EXISTS "Notifications" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "recipientUserId" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "actorUserId" TEXT NOT NULL DEFAULT '',
  "subjectId" TEXT NOT NULL DEFAULT '',
  "message" TEXT NOT NULL DEFAULT '',
  "read" BOOLEAN NOT NULL DEFAULT FALSE,
  "readAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Notifications_org_recipient_read_idx" ON "Notifications"("organizationId", "recipientUserId", "read");
CREATE INDEX IF NOT EXISTS "Notifications_recipient_createdAt_idx" ON "Notifications"("recipientUserId", "createdAt" DESC);
