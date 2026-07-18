-- Phase 5 Sprint 9 — AI Cinematic Director & Auto Filmmaker Engine (UP)

CREATE TABLE IF NOT EXISTS "DirectorJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "projectId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "formatType" TEXT,
  "genre" TEXT,
  "sceneCount" INTEGER,
  "shotCount" INTEGER,
  "runtimeSec" DOUBLE PRECISION,
  "accuracyScore" DOUBLE PRECISION,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "version" INTEGER NOT NULL DEFAULT 1,
  "analysisJson" JSONB,
  "productionJson" JSONB,
  "integrationsJson" JSONB,
  "metadata" JSONB,
  "error" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "DirectorJob_projectId_idx" ON "DirectorJob"("projectId");
CREATE INDEX IF NOT EXISTS "DirectorJob_backendJobId_idx" ON "DirectorJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "DirectorJob_status_idx" ON "DirectorJob"("status");
CREATE INDEX IF NOT EXISTS "DirectorJob_formatType_idx" ON "DirectorJob"("formatType");
CREATE INDEX IF NOT EXISTS "DirectorJob_createdAt_idx" ON "DirectorJob"("createdAt" DESC);

CREATE TABLE IF NOT EXISTS "ProductionPlanRecord" (
  "id" TEXT PRIMARY KEY,
  "directorJobId" TEXT,
  "planId" TEXT NOT NULL,
  "projectId" TEXT,
  "formatType" TEXT,
  "runtimeSec" DOUBLE PRECISION,
  "shotCount" INTEGER,
  "accuracyScore" DOUBLE PRECISION,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ProductionPlanRecord_planId_idx" ON "ProductionPlanRecord"("planId");
CREATE INDEX IF NOT EXISTS "ProductionPlanRecord_projectId_idx" ON "ProductionPlanRecord"("projectId");
CREATE INDEX IF NOT EXISTS "ProductionPlanRecord_directorJobId_idx" ON "ProductionPlanRecord"("directorJobId");

CREATE TABLE IF NOT EXISTS "ScenePlanRecord" (
  "id" TEXT PRIMARY KEY,
  "directorJobId" TEXT,
  "sceneId" TEXT NOT NULL,
  "beat" TEXT,
  "orderIndex" INTEGER,
  "environment" TEXT,
  "emotionFlow" TEXT,
  "durationSec" DOUBLE PRECISION,
  "importance" DOUBLE PRECISION,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ScenePlanRecord_sceneId_idx" ON "ScenePlanRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "ScenePlanRecord_beat_idx" ON "ScenePlanRecord"("beat");
CREATE INDEX IF NOT EXISTS "ScenePlanRecord_directorJobId_idx" ON "ScenePlanRecord"("directorJobId");

CREATE TABLE IF NOT EXISTS "ShotPlanRecord" (
  "id" TEXT PRIMARY KEY,
  "directorJobId" TEXT,
  "shotId" TEXT NOT NULL,
  "sceneId" TEXT,
  "orderIndex" INTEGER,
  "cameraAngle" TEXT,
  "durationSec" DOUBLE PRECISION,
  "emotion" TEXT,
  "transition" TEXT,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ShotPlanRecord_shotId_idx" ON "ShotPlanRecord"("shotId");
CREATE INDEX IF NOT EXISTS "ShotPlanRecord_sceneId_idx" ON "ShotPlanRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "ShotPlanRecord_cameraAngle_idx" ON "ShotPlanRecord"("cameraAngle");
CREATE INDEX IF NOT EXISTS "ShotPlanRecord_directorJobId_idx" ON "ShotPlanRecord"("directorJobId");

CREATE TABLE IF NOT EXISTS "StoryMetadataRecord" (
  "id" TEXT PRIMARY KEY,
  "directorJobId" TEXT,
  "projectId" TEXT,
  "genre" TEXT,
  "formatType" TEXT,
  "targetAudience" TEXT,
  "visualComplexity" DOUBLE PRECISION,
  "audioComplexity" DOUBLE PRECISION,
  "estimatedRuntime" DOUBLE PRECISION,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "StoryMetadataRecord_projectId_idx" ON "StoryMetadataRecord"("projectId");
CREATE INDEX IF NOT EXISTS "StoryMetadataRecord_genre_idx" ON "StoryMetadataRecord"("genre");
CREATE INDEX IF NOT EXISTS "StoryMetadataRecord_formatType_idx" ON "StoryMetadataRecord"("formatType");
CREATE INDEX IF NOT EXISTS "StoryMetadataRecord_directorJobId_idx" ON "StoryMetadataRecord"("directorJobId");

CREATE TABLE IF NOT EXISTS "RuntimeReportRecord" (
  "id" TEXT PRIMARY KEY,
  "directorJobId" TEXT,
  "projectId" TEXT,
  "runtimeSec" DOUBLE PRECISION,
  "sceneCount" INTEGER,
  "shotCount" INTEGER,
  "accuracyScore" DOUBLE PRECISION,
  "passRate" DOUBLE PRECISION,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "RuntimeReportRecord_projectId_idx" ON "RuntimeReportRecord"("projectId");
CREATE INDEX IF NOT EXISTS "RuntimeReportRecord_directorJobId_idx" ON "RuntimeReportRecord"("directorJobId");
CREATE INDEX IF NOT EXISTS "RuntimeReportRecord_createdAt_idx" ON "RuntimeReportRecord"("createdAt" DESC);

CREATE TABLE IF NOT EXISTS "DirectorHistoryRecord" (
  "id" TEXT PRIMARY KEY,
  "directorJobId" TEXT,
  "projectId" TEXT NOT NULL,
  "formatType" TEXT,
  "genre" TEXT,
  "sceneCount" INTEGER,
  "shotCount" INTEGER,
  "runtimeSec" DOUBLE PRECISION,
  "accuracyScore" DOUBLE PRECISION,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "DirectorHistoryRecord_projectId_createdAt_idx" ON "DirectorHistoryRecord"("projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "DirectorHistoryRecord_directorJobId_idx" ON "DirectorHistoryRecord"("directorJobId");
