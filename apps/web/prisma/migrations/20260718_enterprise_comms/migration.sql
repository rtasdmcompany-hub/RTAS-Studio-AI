-- Phase 7 Sprint 6 — Enterprise Notifications, Comments & Activity Engine (UP)

CREATE TABLE IF NOT EXISTS "CollabNotification" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "recipientId" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "body" TEXT,
  "resourceType" TEXT,
  "resourceId" TEXT,
  "actorId" TEXT,
  "isRead" BOOLEAN NOT NULL DEFAULT false,
  "readAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabNotification_recipientId_isRead_createdAt_idx"
  ON "CollabNotification"("recipientId", "isRead", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabNotification_organizationId_createdAt_idx"
  ON "CollabNotification"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabNotification_type_idx" ON "CollabNotification"("type");
CREATE INDEX IF NOT EXISTS "CollabNotification_resourceType_resourceId_idx"
  ON "CollabNotification"("resourceType", "resourceId");

CREATE TABLE IF NOT EXISTS "CollabNotificationPreference" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT,
  "channelEmail" BOOLEAN NOT NULL DEFAULT true,
  "channelInApp" BOOLEAN NOT NULL DEFAULT true,
  "mutedTypesJson" JSONB,
  "digestsEnabled" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CollabNotificationPreference_userId_organizationId_key" UNIQUE ("userId", "organizationId")
);
CREATE INDEX IF NOT EXISTS "CollabNotificationPreference_userId_idx" ON "CollabNotificationPreference"("userId");

CREATE TABLE IF NOT EXISTS "CollabComment" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "authorId" TEXT NOT NULL,
  "resourceType" TEXT NOT NULL,
  "resourceId" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "isPinned" BOOLEAN NOT NULL DEFAULT false,
  "isResolved" BOOLEAN NOT NULL DEFAULT false,
  "reactionsJson" JSONB,
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabComment_organizationId_resourceType_resourceId_createdAt_idx"
  ON "CollabComment"("organizationId", "resourceType", "resourceId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabComment_authorId_idx" ON "CollabComment"("authorId");
CREATE INDEX IF NOT EXISTS "CollabComment_isPinned_idx" ON "CollabComment"("isPinned");
CREATE INDEX IF NOT EXISTS "CollabComment_deletedAt_idx" ON "CollabComment"("deletedAt");

CREATE TABLE IF NOT EXISTS "CollabCommentReply" (
  "id" TEXT PRIMARY KEY,
  "commentId" TEXT NOT NULL,
  "authorId" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabCommentReply_commentId_createdAt_idx"
  ON "CollabCommentReply"("commentId", "createdAt" ASC);
CREATE INDEX IF NOT EXISTS "CollabCommentReply_authorId_idx" ON "CollabCommentReply"("authorId");

CREATE TABLE IF NOT EXISTS "CollabMention" (
  "id" TEXT PRIMARY KEY,
  "commentId" TEXT,
  "organizationId" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "subjectType" TEXT NOT NULL,
  "subjectId" TEXT NOT NULL,
  "targetUserId" TEXT,
  "resourceType" TEXT,
  "resourceId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabMention_organizationId_createdAt_idx"
  ON "CollabMention"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabMention_targetUserId_idx" ON "CollabMention"("targetUserId");
CREATE INDEX IF NOT EXISTS "CollabMention_subjectType_subjectId_idx"
  ON "CollabMention"("subjectType", "subjectId");
CREATE INDEX IF NOT EXISTS "CollabMention_commentId_idx" ON "CollabMention"("commentId");

CREATE TABLE IF NOT EXISTS "CollabActivityEvent" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "actorId" TEXT,
  "category" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "summary" TEXT NOT NULL,
  "resourceType" TEXT,
  "resourceId" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabActivityEvent_organizationId_createdAt_idx"
  ON "CollabActivityEvent"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabActivityEvent_workspaceId_createdAt_idx"
  ON "CollabActivityEvent"("workspaceId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabActivityEvent_actorId_idx" ON "CollabActivityEvent"("actorId");
CREATE INDEX IF NOT EXISTS "CollabActivityEvent_category_action_idx"
  ON "CollabActivityEvent"("category", "action");
CREATE INDEX IF NOT EXISTS "CollabActivityEvent_resourceType_resourceId_idx"
  ON "CollabActivityEvent"("resourceType", "resourceId");

CREATE TABLE IF NOT EXISTS "CollabAnnouncement" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "authorId" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "scope" TEXT NOT NULL DEFAULT 'organization',
  "isPinned" BOOLEAN NOT NULL DEFAULT false,
  "publishedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "expiresAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabAnnouncement_organizationId_publishedAt_idx"
  ON "CollabAnnouncement"("organizationId", "publishedAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabAnnouncement_workspaceId_idx" ON "CollabAnnouncement"("workspaceId");
CREATE INDEX IF NOT EXISTS "CollabAnnouncement_scope_idx" ON "CollabAnnouncement"("scope");

CREATE TABLE IF NOT EXISTS "CollabUserActivityLog" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organizationId" TEXT,
  "workspaceId" TEXT,
  "action" TEXT NOT NULL,
  "detail" TEXT,
  "ipHash" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CollabUserActivityLog_userId_createdAt_idx"
  ON "CollabUserActivityLog"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabUserActivityLog_organizationId_createdAt_idx"
  ON "CollabUserActivityLog"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CollabUserActivityLog_action_idx" ON "CollabUserActivityLog"("action");
