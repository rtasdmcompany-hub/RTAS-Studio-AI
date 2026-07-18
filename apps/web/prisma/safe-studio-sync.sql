-- Safe partial sync: add RTAS Studio tables without dropping existing Supabase tables.

DO $$ BEGIN
  CREATE TYPE "GenerationJobStatus" AS ENUM (
    'QUEUED',
    'GENERATING_CHUNKS',
    'COMPILING_MEDIA',
    'COMPLETED',
    'FAILED'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "passwordHash" TEXT,
    "image" TEXT,
    "provider" TEXT NOT NULL DEFAULT 'credentials',
    "emailVerified" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "tier" TEXT NOT NULL DEFAULT 'free',
    "credits" INTEGER NOT NULL DEFAULT 50,
    "concurrentTracks" INTEGER NOT NULL DEFAULT 0,
    "creditsExpireAt" TIMESTAMP(3),
    "subscriptionActive" BOOLEAN NOT NULL DEFAULT false,
    "subscriptionRenewsAt" TIMESTAMP(3),
    "freeTrialUsed" BOOLEAN NOT NULL DEFAULT false,
    "hasUsedFreeTrial" BOOLEAN NOT NULL DEFAULT false,
    "previewSkipsRemaining" INTEGER NOT NULL DEFAULT 3,
    "paymentProvider" TEXT,
    "externalCustomerId" TEXT,
    "externalSubscriptionId" TEXT,
    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "User_email_key" ON "User"("email");

CREATE TABLE IF NOT EXISTS "GenerationJob" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "status" "GenerationJobStatus" NOT NULL DEFAULT 'QUEUED',
    "prompt" TEXT,
    "inputImageUrl" TEXT,
    "generatedVideoUrl" TEXT,
    "durationSeconds" INTEGER NOT NULL DEFAULT 0,
    "creditsCharged" INTEGER NOT NULL DEFAULT 0,
    "chunkTotal" INTEGER,
    "chunksCompleted" INTEGER,
    "chunkManifest" JSONB,
    "errorMessage" TEXT,
    "backendJobId" TEXT,
    "isPublic" BOOLEAN NOT NULL DEFAULT false,
    "shareTitle" TEXT,
    "publishedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" TIMESTAMP(3),
    CONSTRAINT "GenerationJob_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "GenerationJob_userId_status_idx"
  ON "GenerationJob"("userId", "status");

CREATE INDEX IF NOT EXISTS "GenerationJob_userId_createdAt_idx"
  ON "GenerationJob"("userId", "createdAt" DESC);

CREATE INDEX IF NOT EXISTS "GenerationJob_isPublic_idx"
  ON "GenerationJob"("isPublic");

DO $$ BEGIN
  ALTER TABLE "GenerationJob"
    ADD CONSTRAINT "GenerationJob_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
-- Phase 7 Sprint 1 — Multi-Tenant SaaS Platform Foundation (UP)

CREATE TABLE IF NOT EXISTS "Organization" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL UNIQUE,
  "ownerId" TEXT NOT NULL,
  "plan" TEXT NOT NULL DEFAULT 'free',
  "status" TEXT NOT NULL DEFAULT 'active',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Organization_ownerId_createdAt_idx" ON "Organization"("ownerId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Organization_status_idx" ON "Organization"("status");

CREATE TABLE IF NOT EXISTS "Workspace" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'active',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Workspace_organizationId_slug_key" UNIQUE ("organizationId", "slug")
);
CREATE INDEX IF NOT EXISTS "Workspace_organizationId_createdAt_idx" ON "Workspace"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Workspace_status_idx" ON "Workspace"("status");

CREATE TABLE IF NOT EXISTS "Team" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'active',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Team_organizationId_slug_key" UNIQUE ("organizationId", "slug")
);
CREATE INDEX IF NOT EXISTS "Team_organizationId_idx" ON "Team"("organizationId");
CREATE INDEX IF NOT EXISTS "Team_workspaceId_idx" ON "Team"("workspaceId");

CREATE TABLE IF NOT EXISTS "Role" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT,
  "key" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "isSystem" BOOLEAN NOT NULL DEFAULT true,
  "rank" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS "Role_organizationId_key_key" ON "Role"("organizationId", "key");
CREATE INDEX IF NOT EXISTS "Role_key_idx" ON "Role"("key");
CREATE INDEX IF NOT EXISTS "Role_isSystem_idx" ON "Role"("isSystem");

CREATE TABLE IF NOT EXISTS "Permission" (
  "id" TEXT PRIMARY KEY,
  "key" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "category" TEXT NOT NULL DEFAULT 'general',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Permission_category_idx" ON "Permission"("category");

CREATE TABLE IF NOT EXISTS "RolePermission" (
  "id" TEXT PRIMARY KEY,
  "roleId" TEXT NOT NULL,
  "permissionId" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RolePermission_roleId_permissionId_key" UNIQUE ("roleId", "permissionId")
);
CREATE INDEX IF NOT EXISTS "RolePermission_permissionId_idx" ON "RolePermission"("permissionId");

CREATE TABLE IF NOT EXISTS "OrganizationMember" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "userId" TEXT NOT NULL,
  "roleId" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'active',
  "joinedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "OrganizationMember_organizationId_userId_key" UNIQUE ("organizationId", "userId")
);
CREATE INDEX IF NOT EXISTS "OrganizationMember_organizationId_roleId_idx" ON "OrganizationMember"("organizationId", "roleId");
CREATE INDEX IF NOT EXISTS "OrganizationMember_userId_idx" ON "OrganizationMember"("userId");
CREATE INDEX IF NOT EXISTS "OrganizationMember_workspaceId_idx" ON "OrganizationMember"("workspaceId");
CREATE INDEX IF NOT EXISTS "OrganizationMember_status_idx" ON "OrganizationMember"("status");

CREATE TABLE IF NOT EXISTS "TeamMember" (
  "id" TEXT PRIMARY KEY,
  "teamId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'active',
  "joinedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "TeamMember_teamId_userId_key" UNIQUE ("teamId", "userId")
);
CREATE INDEX IF NOT EXISTS "TeamMember_userId_idx" ON "TeamMember"("userId");
CREATE INDEX IF NOT EXISTS "TeamMember_teamId_idx" ON "TeamMember"("teamId");

CREATE TABLE IF NOT EXISTS "Invite" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "email" TEXT NOT NULL,
  "roleId" TEXT NOT NULL,
  "token" TEXT NOT NULL UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "invitedById" TEXT NOT NULL,
  "expiresAt" TIMESTAMP(3) NOT NULL,
  "acceptedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Invite_organizationId_status_idx" ON "Invite"("organizationId", "status");
CREATE INDEX IF NOT EXISTS "Invite_email_status_idx" ON "Invite"("email", "status");
CREATE INDEX IF NOT EXISTS "Invite_token_idx" ON "Invite"("token");
CREATE INDEX IF NOT EXISTS "Invite_expiresAt_idx" ON "Invite"("expiresAt");

-- Phase 7 Sprint 3 — Organization, Workspace & Team Management Engine
ALTER TABLE "TeamMember" ADD COLUMN IF NOT EXISTS "teamRole" TEXT NOT NULL DEFAULT 'member';
ALTER TABLE "TeamMember" ADD COLUMN IF NOT EXISTS "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX IF NOT EXISTS "TeamMember_teamRole_idx" ON "TeamMember"("teamRole");

CREATE TABLE IF NOT EXISTS "OrganizationSettings" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL UNIQUE,
  "timezone" TEXT NOT NULL DEFAULT 'UTC',
  "locale" TEXT NOT NULL DEFAULT 'en',
  "allowInvites" BOOLEAN NOT NULL DEFAULT true,
  "defaultRole" TEXT NOT NULL DEFAULT 'viewer',
  "settingsJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "WorkspaceSettings" (
  "id" TEXT PRIMARY KEY,
  "workspaceId" TEXT NOT NULL UNIQUE,
  "visibility" TEXT NOT NULL DEFAULT 'private',
  "defaultModel" TEXT,
  "settingsJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "TeamActivityLog" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "teamId" TEXT,
  "actorId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "detail" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TeamActivityLog_organizationId_createdAt_idx"
  ON "TeamActivityLog"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "TeamActivityLog_workspaceId_createdAt_idx"
  ON "TeamActivityLog"("workspaceId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "TeamActivityLog_teamId_createdAt_idx"
  ON "TeamActivityLog"("teamId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "TeamActivityLog_actorId_idx" ON "TeamActivityLog"("actorId");
CREATE INDEX IF NOT EXISTS "TeamActivityLog_action_idx" ON "TeamActivityLog"("action");

-- Phase 7 Sprint 4 — Project Management & Collaboration Engine
CREATE TABLE IF NOT EXISTS "OrgProjectTemplate" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT,
  "key" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "defaultStatus" TEXT NOT NULL DEFAULT 'draft',
  "blueprintJson" JSONB,
  "isSystem" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS "OrgProjectTemplate_organizationId_key_key"
  ON "OrgProjectTemplate"("organizationId", "key");
CREATE INDEX IF NOT EXISTS "OrgProjectTemplate_isSystem_idx" ON "OrgProjectTemplate"("isSystem");

CREATE TABLE IF NOT EXISTS "OrgProject" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ownerId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "description" TEXT,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "isFavorite" BOOLEAN NOT NULL DEFAULT false,
  "isShared" BOOLEAN NOT NULL DEFAULT false,
  "templateId" TEXT,
  "metadataJson" JSONB,
  "archivedAt" TIMESTAMP(3),
  "deletedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "OrgProject_organizationId_slug_key" UNIQUE ("organizationId", "slug")
);
CREATE INDEX IF NOT EXISTS "OrgProject_organizationId_status_createdAt_idx"
  ON "OrgProject"("organizationId", "status", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProject_workspaceId_status_idx" ON "OrgProject"("workspaceId", "status");
CREATE INDEX IF NOT EXISTS "OrgProject_ownerId_idx" ON "OrgProject"("ownerId");
CREATE INDEX IF NOT EXISTS "OrgProject_isFavorite_idx" ON "OrgProject"("isFavorite");
CREATE INDEX IF NOT EXISTS "OrgProject_deletedAt_idx" ON "OrgProject"("deletedAt");

CREATE TABLE IF NOT EXISTS "OrgProjectMember" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "roleKey" TEXT NOT NULL DEFAULT 'contributor',
  "status" TEXT NOT NULL DEFAULT 'active',
  "joinedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "OrgProjectMember_projectId_userId_key" UNIQUE ("projectId", "userId")
);
CREATE INDEX IF NOT EXISTS "OrgProjectMember_userId_idx" ON "OrgProjectMember"("userId");
CREATE INDEX IF NOT EXISTS "OrgProjectMember_projectId_roleKey_idx" ON "OrgProjectMember"("projectId", "roleKey");
CREATE INDEX IF NOT EXISTS "OrgProjectMember_status_idx" ON "OrgProjectMember"("status");

CREATE TABLE IF NOT EXISTS "OrgProjectRole" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT,
  "key" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "isSystem" BOOLEAN NOT NULL DEFAULT true,
  "permissions" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS "OrgProjectRole_projectId_key_key" ON "OrgProjectRole"("projectId", "key");
CREATE INDEX IF NOT EXISTS "OrgProjectRole_key_idx" ON "OrgProjectRole"("key");

CREATE TABLE IF NOT EXISTS "OrgProjectActivity" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "detail" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectActivity_projectId_createdAt_idx"
  ON "OrgProjectActivity"("projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectActivity_actorId_idx" ON "OrgProjectActivity"("actorId");
CREATE INDEX IF NOT EXISTS "OrgProjectActivity_action_idx" ON "OrgProjectActivity"("action");

CREATE TABLE IF NOT EXISTS "OrgProjectTimeline" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "summary" TEXT NOT NULL,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectTimeline_projectId_createdAt_idx"
  ON "OrgProjectTimeline"("projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectTimeline_eventType_idx" ON "OrgProjectTimeline"("eventType");

CREATE TABLE IF NOT EXISTS "OrgProjectSettings" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT NOT NULL UNIQUE,
  "visibility" TEXT NOT NULL DEFAULT 'private',
  "allowComments" BOOLEAN NOT NULL DEFAULT true,
  "allowTasks" BOOLEAN NOT NULL DEFAULT true,
  "settingsJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "OrgProjectNote" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT NOT NULL,
  "authorId" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "isInternal" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectNote_projectId_createdAt_idx"
  ON "OrgProjectNote"("projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectNote_authorId_idx" ON "OrgProjectNote"("authorId");

CREATE TABLE IF NOT EXISTS "OrgProjectTask" (
  "id" TEXT PRIMARY KEY,
  "projectId" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT,
  "status" TEXT NOT NULL DEFAULT 'open',
  "assigneeId" TEXT,
  "createdById" TEXT NOT NULL,
  "dueAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectTask_projectId_status_idx" ON "OrgProjectTask"("projectId", "status");
CREATE INDEX IF NOT EXISTS "OrgProjectTask_assigneeId_idx" ON "OrgProjectTask"("assigneeId");

-- Phase 7 Sprint 5 — Enterprise Asset Management & Digital Library Engine
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

-- Phase 7 Sprint 6 � Enterprise Notifications, Comments & Activity Engine
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
-- Phase 7 Sprint 7 — Enterprise Version Control, Approval & Review Engine (UP)

CREATE TABLE IF NOT EXISTS "OrgProjectVersion" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "projectId" TEXT NOT NULL,
  "versionNumber" INTEGER NOT NULL,
  "label" TEXT,
  "notes" TEXT,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "createdById" TEXT NOT NULL,
  "parentVersionId" TEXT,
  "isCurrent" BOOLEAN NOT NULL DEFAULT false,
  "snapshotJson" JSONB,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "OrgProjectVersion_projectId_versionNumber_key" UNIQUE ("projectId", "versionNumber")
);
CREATE INDEX IF NOT EXISTS "OrgProjectVersion_organizationId_projectId_createdAt_idx"
  ON "OrgProjectVersion"("organizationId", "projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectVersion_workspaceId_idx" ON "OrgProjectVersion"("workspaceId");
CREATE INDEX IF NOT EXISTS "OrgProjectVersion_status_idx" ON "OrgProjectVersion"("status");
CREATE INDEX IF NOT EXISTS "OrgProjectVersion_isCurrent_idx" ON "OrgProjectVersion"("isCurrent");

CREATE TABLE IF NOT EXISTS "VersionSnapshot" (
  "id" TEXT PRIMARY KEY,
  "versionId" TEXT NOT NULL,
  "name" TEXT,
  "payloadJson" JSONB NOT NULL,
  "checksum" TEXT,
  "sizeBytes" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VersionSnapshot_versionId_createdAt_idx"
  ON "VersionSnapshot"("versionId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "OrgProjectApprovalRequest" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "projectId" TEXT NOT NULL,
  "versionId" TEXT,
  "requestedById" TEXT NOT NULL,
  "reviewerId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'pending_review',
  "scope" TEXT NOT NULL DEFAULT 'internal',
  "title" TEXT,
  "notes" TEXT,
  "decidedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectApprovalRequest_organizationId_projectId_createdAt_idx"
  ON "OrgProjectApprovalRequest"("organizationId", "projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectApprovalRequest_status_idx" ON "OrgProjectApprovalRequest"("status");
CREATE INDEX IF NOT EXISTS "OrgProjectApprovalRequest_reviewerId_idx" ON "OrgProjectApprovalRequest"("reviewerId");
CREATE INDEX IF NOT EXISTS "OrgProjectApprovalRequest_versionId_idx" ON "OrgProjectApprovalRequest"("versionId");

CREATE TABLE IF NOT EXISTS "OrgProjectApprovalHistory" (
  "id" TEXT PRIMARY KEY,
  "approvalId" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "fromStatus" TEXT,
  "toStatus" TEXT NOT NULL,
  "note" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectApprovalHistory_approvalId_createdAt_idx"
  ON "OrgProjectApprovalHistory"("approvalId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectApprovalHistory_actorId_idx" ON "OrgProjectApprovalHistory"("actorId");

CREATE TABLE IF NOT EXISTS "OrgProjectReview" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "projectId" TEXT NOT NULL,
  "versionId" TEXT,
  "approvalId" TEXT,
  "createdById" TEXT NOT NULL,
  "assigneeId" TEXT,
  "reviewType" TEXT NOT NULL DEFAULT 'internal',
  "status" TEXT NOT NULL DEFAULT 'pending_review',
  "summary" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectReview_organizationId_projectId_createdAt_idx"
  ON "OrgProjectReview"("organizationId", "projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectReview_assigneeId_idx" ON "OrgProjectReview"("assigneeId");
CREATE INDEX IF NOT EXISTS "OrgProjectReview_status_idx" ON "OrgProjectReview"("status");
CREATE INDEX IF NOT EXISTS "OrgProjectReview_reviewType_idx" ON "OrgProjectReview"("reviewType");

CREATE TABLE IF NOT EXISTS "OrgProjectReviewComment" (
  "id" TEXT PRIMARY KEY,
  "reviewId" TEXT NOT NULL,
  "authorId" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectReviewComment_reviewId_createdAt_idx"
  ON "OrgProjectReviewComment"("reviewId", "createdAt" ASC);
CREATE INDEX IF NOT EXISTS "OrgProjectReviewComment_authorId_idx" ON "OrgProjectReviewComment"("authorId");

CREATE TABLE IF NOT EXISTS "OrgProjectChangeLog" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "projectId" TEXT NOT NULL,
  "actorId" TEXT,
  "changeType" TEXT NOT NULL,
  "summary" TEXT NOT NULL,
  "beforeJson" JSONB,
  "afterJson" JSONB,
  "metadataJson" JSONB,
  "versionId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectChangeLog_organizationId_projectId_createdAt_idx"
  ON "OrgProjectChangeLog"("organizationId", "projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectChangeLog_changeType_idx" ON "OrgProjectChangeLog"("changeType");
CREATE INDEX IF NOT EXISTS "OrgProjectChangeLog_actorId_idx" ON "OrgProjectChangeLog"("actorId");

CREATE TABLE IF NOT EXISTS "OrgProjectRollbackHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "projectId" TEXT NOT NULL,
  "fromVersionId" TEXT,
  "toVersionId" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "note" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrgProjectRollbackHistory_organizationId_projectId_createdAt_idx"
  ON "OrgProjectRollbackHistory"("organizationId", "projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OrgProjectRollbackHistory_actorId_idx" ON "OrgProjectRollbackHistory"("actorId");
CREATE INDEX IF NOT EXISTS "OrgProjectRollbackHistory_toVersionId_idx" ON "OrgProjectRollbackHistory"("toVersionId");


