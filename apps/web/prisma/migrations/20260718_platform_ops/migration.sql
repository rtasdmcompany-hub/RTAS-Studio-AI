-- Phase 7 Sprint 9 — Enterprise Administration, System Management & Platform Operations (UP)

CREATE TABLE IF NOT EXISTS "PlatformSetting" (
  "id" TEXT PRIMARY KEY,
  "key" TEXT NOT NULL UNIQUE,
  "category" TEXT NOT NULL DEFAULT 'general',
  "valueJson" JSONB,
  "isSecret" BOOLEAN NOT NULL DEFAULT false,
  "description" TEXT,
  "updatedById" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PlatformSetting_category_idx" ON "PlatformSetting"("category");

CREATE TABLE IF NOT EXISTS "SystemConfiguration" (
  "id" TEXT PRIMARY KEY,
  "namespace" TEXT NOT NULL UNIQUE,
  "configJson" JSONB,
  "environment" TEXT NOT NULL DEFAULT 'production',
  "isValid" BOOLEAN NOT NULL DEFAULT true,
  "validatedAt" TIMESTAMP(3),
  "validationMsg" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SystemConfiguration_environment_idx" ON "SystemConfiguration"("environment");

CREATE TABLE IF NOT EXISTS "FeatureFlag" (
  "id" TEXT PRIMARY KEY,
  "key" TEXT NOT NULL UNIQUE,
  "enabled" BOOLEAN NOT NULL DEFAULT false,
  "description" TEXT,
  "rolloutPercent" INTEGER NOT NULL DEFAULT 100,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "FeatureFlag_enabled_idx" ON "FeatureFlag"("enabled");

CREATE TABLE IF NOT EXISTS "MaintenanceEvent" (
  "id" TEXT PRIMARY KEY,
  "status" TEXT NOT NULL DEFAULT 'scheduled',
  "message" TEXT NOT NULL,
  "startsAt" TIMESTAMP(3),
  "endsAt" TIMESTAMP(3),
  "createdById" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MaintenanceEvent_status_createdAt_idx"
  ON "MaintenanceEvent"("status", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "AdminActivity" (
  "id" TEXT PRIMARY KEY,
  "actorId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "detail" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AdminActivity_actorId_createdAt_idx"
  ON "AdminActivity"("actorId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AdminActivity_action_idx" ON "AdminActivity"("action");

CREATE TABLE IF NOT EXISTS "SystemLog" (
  "id" TEXT PRIMARY KEY,
  "level" TEXT NOT NULL DEFAULT 'info',
  "source" TEXT NOT NULL,
  "message" TEXT NOT NULL,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SystemLog_level_createdAt_idx" ON "SystemLog"("level", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "SystemLog_source_createdAt_idx" ON "SystemLog"("source", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "ScheduledTask" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL UNIQUE,
  "cronExpr" TEXT,
  "status" TEXT NOT NULL DEFAULT 'idle',
  "lastRunAt" TIMESTAMP(3),
  "nextRunAt" TIMESTAMP(3),
  "updatedById" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ScheduledTask_status_idx" ON "ScheduledTask"("status");

CREATE TABLE IF NOT EXISTS "OperationsHistory" (
  "id" TEXT PRIMARY KEY,
  "operation" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'success',
  "actorId" TEXT,
  "detail" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OperationsHistory_operation_createdAt_idx"
  ON "OperationsHistory"("operation", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "OperationsHistory_actorId_idx" ON "OperationsHistory"("actorId");
CREATE INDEX IF NOT EXISTS "OperationsHistory_status_idx" ON "OperationsHistory"("status");
