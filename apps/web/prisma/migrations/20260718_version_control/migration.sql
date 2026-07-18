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
