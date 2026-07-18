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
