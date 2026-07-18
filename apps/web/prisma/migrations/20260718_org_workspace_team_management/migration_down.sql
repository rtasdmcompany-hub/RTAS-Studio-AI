-- Phase 7 Sprint 3 — Organization, Workspace & Team Management Engine (DOWN)

DROP TABLE IF EXISTS "TeamActivityLog";
DROP TABLE IF EXISTS "WorkspaceSettings";
DROP TABLE IF EXISTS "OrganizationSettings";
DROP INDEX IF EXISTS "TeamMember_teamRole_idx";
ALTER TABLE "TeamMember" DROP COLUMN IF EXISTS "updatedAt";
ALTER TABLE "TeamMember" DROP COLUMN IF EXISTS "teamRole";
