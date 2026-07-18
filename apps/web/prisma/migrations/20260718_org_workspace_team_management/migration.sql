-- Phase 7 Sprint 3 — Organization, Workspace & Team Management Engine (UP)

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
