-- Phase 9 Sprint 7 — AI Agents, Automation Workflows & Orchestration (UP)

CREATE TABLE IF NOT EXISTS "AIAgents" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "agentType" TEXT NOT NULL DEFAULT 'custom',
  "description" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'active',
  "capabilitiesJson" JSONB,
  "configJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AIAgents_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AIAgents_organizationId_idx" ON "AIAgents"("organizationId");
CREATE INDEX IF NOT EXISTS "AIAgents_workspaceId_idx" ON "AIAgents"("workspaceId");
CREATE INDEX IF NOT EXISTS "AIAgents_ownerUserId_idx" ON "AIAgents"("ownerUserId");
CREATE INDEX IF NOT EXISTS "AIAgents_agentType_idx" ON "AIAgents"("agentType");
CREATE INDEX IF NOT EXISTS "AIAgents_status_idx" ON "AIAgents"("status");

CREATE TABLE IF NOT EXISTS "AgentWorkflowTemplates" (
  "id" TEXT PRIMARY KEY,
  "slug" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "mode" TEXT NOT NULL DEFAULT 'sequential',
  "agentTypesJson" JSONB,
  "stepsJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AgentWorkflowTemplates_slug_key" UNIQUE ("slug")
);

CREATE TABLE IF NOT EXISTS "AgentWorkflows" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "ownerUserId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "trigger" TEXT NOT NULL DEFAULT 'manual',
  "mode" TEXT NOT NULL DEFAULT 'sequential',
  "status" TEXT NOT NULL DEFAULT 'active',
  "stepsJson" JSONB,
  "conditionsJson" JSONB,
  "templateId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AgentWorkflows_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "AgentWorkflows_templateId_fkey" FOREIGN KEY ("templateId")
    REFERENCES "AgentWorkflowTemplates"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "AgentWorkflows_organizationId_idx" ON "AgentWorkflows"("organizationId");
CREATE INDEX IF NOT EXISTS "AgentWorkflows_workspaceId_idx" ON "AgentWorkflows"("workspaceId");
CREATE INDEX IF NOT EXISTS "AgentWorkflows_status_idx" ON "AgentWorkflows"("status");
CREATE INDEX IF NOT EXISTS "AgentWorkflows_templateId_idx" ON "AgentWorkflows"("templateId");

CREATE TABLE IF NOT EXISTS "WorkflowExecutions" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "workflowId" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "trigger" TEXT NOT NULL DEFAULT 'manual',
  "startedBy" TEXT NOT NULL DEFAULT '',
  "contextJson" JSONB,
  "resultsJson" JSONB,
  "error" TEXT NOT NULL DEFAULT '',
  "retries" INTEGER NOT NULL DEFAULT 0,
  "maxRetries" INTEGER NOT NULL DEFAULT 3,
  "priority" TEXT NOT NULL DEFAULT 'normal',
  "startedAt" TIMESTAMP(3),
  "completedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "WorkflowExecutions_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "WorkflowExecutions_workflowId_fkey" FOREIGN KEY ("workflowId")
    REFERENCES "AgentWorkflows"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "WorkflowExecutions_organizationId_createdAt_idx"
  ON "WorkflowExecutions"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "WorkflowExecutions_workflowId_idx" ON "WorkflowExecutions"("workflowId");
CREATE INDEX IF NOT EXISTS "WorkflowExecutions_status_idx" ON "WorkflowExecutions"("status");

CREATE TABLE IF NOT EXISTS "AgentMemory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "agentId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "key" TEXT NOT NULL,
  "valueJson" JSONB,
  "executionId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AgentMemory_agentId_key_key" UNIQUE ("agentId", "key"),
  CONSTRAINT "AgentMemory_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "AgentMemory_agentId_fkey" FOREIGN KEY ("agentId")
    REFERENCES "AIAgents"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AgentMemory_organizationId_idx" ON "AgentMemory"("organizationId");
CREATE INDEX IF NOT EXISTS "AgentMemory_agentId_idx" ON "AgentMemory"("agentId");

CREATE TABLE IF NOT EXISTS "ScheduledJobs" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "workflowId" TEXT NOT NULL,
  "kind" TEXT NOT NULL DEFAULT 'once',
  "cron" TEXT NOT NULL DEFAULT '',
  "priority" TEXT NOT NULL DEFAULT 'normal',
  "status" TEXT NOT NULL DEFAULT 'scheduled',
  "nextRunAt" TIMESTAMP(3),
  "lastRunAt" TIMESTAMP(3),
  "maxRetries" INTEGER NOT NULL DEFAULT 3,
  "createdBy" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ScheduledJobs_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "ScheduledJobs_workflowId_fkey" FOREIGN KEY ("workflowId")
    REFERENCES "AgentWorkflows"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "ScheduledJobs_organizationId_idx" ON "ScheduledJobs"("organizationId");
CREATE INDEX IF NOT EXISTS "ScheduledJobs_workflowId_idx" ON "ScheduledJobs"("workflowId");
CREATE INDEX IF NOT EXISTS "ScheduledJobs_status_idx" ON "ScheduledJobs"("status");
CREATE INDEX IF NOT EXISTS "ScheduledJobs_nextRunAt_idx" ON "ScheduledJobs"("nextRunAt");

CREATE TABLE IF NOT EXISTS "ExecutionHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "executionId" TEXT NOT NULL,
  "workflowId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "message" TEXT NOT NULL DEFAULT '',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ExecutionHistory_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "ExecutionHistory_executionId_fkey" FOREIGN KEY ("executionId")
    REFERENCES "WorkflowExecutions"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "ExecutionHistory_organizationId_createdAt_idx"
  ON "ExecutionHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ExecutionHistory_executionId_idx" ON "ExecutionHistory"("executionId");
CREATE INDEX IF NOT EXISTS "ExecutionHistory_workflowId_idx" ON "ExecutionHistory"("workflowId");
CREATE INDEX IF NOT EXISTS "ExecutionHistory_eventType_idx" ON "ExecutionHistory"("eventType");

CREATE TABLE IF NOT EXISTS "AgentEvents" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "agentId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "payloadJson" JSONB,
  "actorUserId" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AgentEvents_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE CASCADE,
  CONSTRAINT "AgentEvents_agentId_fkey" FOREIGN KEY ("agentId")
    REFERENCES "AIAgents"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "AgentEvents_organizationId_createdAt_idx"
  ON "AgentEvents"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AgentEvents_agentId_idx" ON "AgentEvents"("agentId");
CREATE INDEX IF NOT EXISTS "AgentEvents_eventType_idx" ON "AgentEvents"("eventType");
