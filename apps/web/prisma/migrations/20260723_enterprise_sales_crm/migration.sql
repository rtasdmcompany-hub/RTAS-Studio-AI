-- Phase 13 Sprint 2 — Enterprise sales CRM (leads, activities, proposals)
-- No seed data — empty pipeline until real inquiries arrive.

CREATE TABLE IF NOT EXISTS "EnterpriseLeads" (
  "id" TEXT PRIMARY KEY,
  "kind" TEXT NOT NULL DEFAULT 'enterprise',
  "name" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "company" TEXT,
  "role" TEXT,
  "website" TEXT,
  "phone" TEXT,
  "teamSize" TEXT,
  "industry" TEXT,
  "requestType" TEXT,
  "demoType" TEXT,
  "message" TEXT,
  "planInterest" TEXT,
  "estimatedValueUsd" DOUBLE PRECISION,
  "stage" TEXT NOT NULL DEFAULT 'new_lead',
  "status" TEXT NOT NULL DEFAULT 'open',
  "priority" TEXT NOT NULL DEFAULT 'medium',
  "owner" TEXT,
  "tags" TEXT NOT NULL DEFAULT '',
  "notes" TEXT,
  "timeline" TEXT,
  "requirements" TEXT,
  "authorizedUse" TEXT NOT NULL DEFAULT 'unknown',
  "source" TEXT NOT NULL DEFAULT 'web_form',
  "lossReason" TEXT,
  "forecastCloseAt" TIMESTAMP(3),
  "ipHash" TEXT,
  "userAgent" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS "EnterpriseLeads_email_createdAt_idx" ON "EnterpriseLeads"("email", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EnterpriseLeads_stage_status_idx" ON "EnterpriseLeads"("stage", "status");
CREATE INDEX IF NOT EXISTS "EnterpriseLeads_priority_createdAt_idx" ON "EnterpriseLeads"("priority", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EnterpriseLeads_owner_idx" ON "EnterpriseLeads"("owner");
CREATE INDEX IF NOT EXISTS "EnterpriseLeads_kind_createdAt_idx" ON "EnterpriseLeads"("kind", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "EnterpriseLeadActivities" (
  "id" TEXT PRIMARY KEY,
  "leadId" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "actor" TEXT NOT NULL DEFAULT 'system',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EnterpriseLeadActivities_leadId_fkey"
    FOREIGN KEY ("leadId") REFERENCES "EnterpriseLeads"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "EnterpriseLeadActivities_leadId_createdAt_idx"
  ON "EnterpriseLeadActivities"("leadId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EnterpriseLeadActivities_type_createdAt_idx"
  ON "EnterpriseLeadActivities"("type", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "EnterpriseProposals" (
  "id" TEXT PRIMARY KEY,
  "proposalNumber" TEXT NOT NULL,
  "leadId" TEXT,
  "customerName" TEXT NOT NULL,
  "customerContact" TEXT,
  "customerEmail" TEXT,
  "requirements" TEXT,
  "solution" TEXT,
  "timeline" TEXT,
  "pricingNotes" TEXT,
  "supportNotes" TEXT,
  "acceptanceNotes" TEXT,
  "markdownBody" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "createdBy" TEXT NOT NULL DEFAULT 'admin',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EnterpriseProposals_leadId_fkey"
    FOREIGN KEY ("leadId") REFERENCES "EnterpriseLeads"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS "EnterpriseProposals_proposalNumber_key" ON "EnterpriseProposals"("proposalNumber");
CREATE INDEX IF NOT EXISTS "EnterpriseProposals_leadId_idx" ON "EnterpriseProposals"("leadId");
CREATE INDEX IF NOT EXISTS "EnterpriseProposals_status_createdAt_idx" ON "EnterpriseProposals"("status", "createdAt" DESC);
