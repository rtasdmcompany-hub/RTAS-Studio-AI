-- Phase 9 Sprint 8 — Enterprise Automation, Integrations & Event-Driven Platform (UP)

CREATE TABLE IF NOT EXISTS "AutomationRules" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "mode" TEXT NOT NULL DEFAULT 'event',
  "status" TEXT NOT NULL DEFAULT 'active',
  "description" TEXT NOT NULL DEFAULT '',
  "triggerEvent" TEXT NOT NULL DEFAULT '',
  "conditionsJson" JSONB,
  "actionsJson" JSONB,
  "integrationId" TEXT,
  "priority" INTEGER NOT NULL DEFAULT 100,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AutomationRules_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AutomationRules_organizationId_idx" ON "AutomationRules"("organizationId");
CREATE INDEX IF NOT EXISTS "AutomationRules_workspaceId_idx" ON "AutomationRules"("workspaceId");
CREATE INDEX IF NOT EXISTS "AutomationRules_status_idx" ON "AutomationRules"("status");
CREATE INDEX IF NOT EXISTS "AutomationRules_triggerEvent_idx" ON "AutomationRules"("triggerEvent");

CREATE TABLE IF NOT EXISTS "AutomationExecutions" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ruleId" TEXT NOT NULL,
  "eventId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "trigger" TEXT NOT NULL DEFAULT 'event',
  "resultsJson" JSONB,
  "error" TEXT NOT NULL DEFAULT '',
  "startedAt" TIMESTAMP(3),
  "completedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AutomationExecutions_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "AutomationExecutions_ruleId_fkey" FOREIGN KEY ("ruleId")
    REFERENCES "AutomationRules"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AutomationExecutions_organizationId_createdAt_idx"
  ON "AutomationExecutions"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AutomationExecutions_ruleId_idx" ON "AutomationExecutions"("ruleId");
CREATE INDEX IF NOT EXISTS "AutomationExecutions_status_idx" ON "AutomationExecutions"("status");

CREATE TABLE IF NOT EXISTS "EventBus" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "eventType" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "payloadJson" JSONB,
  "actorUserId" TEXT NOT NULL DEFAULT '',
  "signature" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'published',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EventBus_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "EventBus_organizationId_createdAt_idx"
  ON "EventBus"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EventBus_eventType_idx" ON "EventBus"("eventType");
CREATE INDEX IF NOT EXISTS "EventBus_category_idx" ON "EventBus"("category");

CREATE TABLE IF NOT EXISTS "EventLogs" (
  "id" TEXT PRIMARY KEY,
  "eventId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "message" TEXT NOT NULL DEFAULT '',
  "success" BOOLEAN NOT NULL DEFAULT TRUE,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EventLogs_eventId_fkey" FOREIGN KEY ("eventId")
    REFERENCES "EventBus"("id") ON DELETE CASCADE,
  CONSTRAINT "EventLogs_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "EventLogs_eventId_createdAt_idx" ON "EventLogs"("eventId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EventLogs_organizationId_idx" ON "EventLogs"("organizationId");
CREATE INDEX IF NOT EXISTS "EventLogs_action_idx" ON "EventLogs"("action");

CREATE TABLE IF NOT EXISTS "EventSubscriptions" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "eventType" TEXT NOT NULL,
  "ruleId" TEXT,
  "target" TEXT NOT NULL DEFAULT 'automation',
  "status" TEXT NOT NULL DEFAULT 'active',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EventSubscriptions_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "EventSubscriptions_ruleId_fkey" FOREIGN KEY ("ruleId")
    REFERENCES "AutomationRules"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "EventSubscriptions_organizationId_idx" ON "EventSubscriptions"("organizationId");
CREATE INDEX IF NOT EXISTS "EventSubscriptions_eventType_idx" ON "EventSubscriptions"("eventType");
CREATE INDEX IF NOT EXISTS "EventSubscriptions_ruleId_idx" ON "EventSubscriptions"("ruleId");

CREATE TABLE IF NOT EXISTS "AutomationIntegrationConnections" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "provider" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'connected',
  "displayName" TEXT NOT NULL DEFAULT '',
  "credentialsRef" TEXT NOT NULL DEFAULT '',
  "webhookSecret" TEXT NOT NULL DEFAULT '',
  "metadataJson" JSONB,
  "connectedBy" TEXT NOT NULL DEFAULT '',
  "connectedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AutomationIntegrationConnections_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AutomationIntegrationConnections_organizationId_idx"
  ON "AutomationIntegrationConnections"("organizationId");
CREATE INDEX IF NOT EXISTS "AutomationIntegrationConnections_workspaceId_idx"
  ON "AutomationIntegrationConnections"("workspaceId");
CREATE INDEX IF NOT EXISTS "AutomationIntegrationConnections_provider_idx"
  ON "AutomationIntegrationConnections"("provider");
CREATE INDEX IF NOT EXISTS "AutomationIntegrationConnections_status_idx"
  ON "AutomationIntegrationConnections"("status");

CREATE TABLE IF NOT EXISTS "ScheduledAutomations" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ruleId" TEXT NOT NULL,
  "kind" TEXT NOT NULL DEFAULT 'once',
  "cron" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'scheduled',
  "nextRunAt" TIMESTAMP(3),
  "lastRunAt" TIMESTAMP(3),
  "createdBy" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ScheduledAutomations_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "ScheduledAutomations_ruleId_fkey" FOREIGN KEY ("ruleId")
    REFERENCES "AutomationRules"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "ScheduledAutomations_organizationId_idx" ON "ScheduledAutomations"("organizationId");
CREATE INDEX IF NOT EXISTS "ScheduledAutomations_ruleId_idx" ON "ScheduledAutomations"("ruleId");
CREATE INDEX IF NOT EXISTS "ScheduledAutomations_status_idx" ON "ScheduledAutomations"("status");
CREATE INDEX IF NOT EXISTS "ScheduledAutomations_nextRunAt_idx" ON "ScheduledAutomations"("nextRunAt");

CREATE TABLE IF NOT EXISTS "AutomationHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "ruleId" TEXT NOT NULL,
  "executionId" TEXT,
  "eventType" TEXT NOT NULL,
  "message" TEXT NOT NULL DEFAULT '',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AutomationHistory_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "AutomationHistory_ruleId_fkey" FOREIGN KEY ("ruleId")
    REFERENCES "AutomationRules"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AutomationHistory_organizationId_createdAt_idx"
  ON "AutomationHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AutomationHistory_ruleId_idx" ON "AutomationHistory"("ruleId");
CREATE INDEX IF NOT EXISTS "AutomationHistory_eventType_idx" ON "AutomationHistory"("eventType");
