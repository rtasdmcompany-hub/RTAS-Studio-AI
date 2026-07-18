-- Phase 7 Sprint 4 — Project Management & Collaboration Engine (UP)

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
