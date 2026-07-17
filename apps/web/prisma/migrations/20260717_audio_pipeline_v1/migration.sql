-- Phase 4 Sprint 10 — Complete AI Audio Production Pipeline v1.0 (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "AudioPipelineJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "prompt" TEXT NOT NULL,
  "platform" TEXT NOT NULL DEFAULT 'youtube',
  "engineVersion" TEXT NOT NULL DEFAULT '1.0.0',
  "qualityScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "qualityPassed" BOOLEAN NOT NULL DEFAULT false,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "stagesCompleted" INTEGER NOT NULL DEFAULT 0,
  "stagesTotal" INTEGER NOT NULL DEFAULT 15,
  "processingTimeMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "queueTimeMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "downloadUrl" TEXT,
  "voiceJobId" TEXT,
  "cloneId" TEXT,
  "musicJobId" TEXT,
  "sfxJobId" TEXT,
  "mixJobId" TEXT,
  "localizationJobId" TEXT,
  "timelineJobId" TEXT,
  "exportJobId" TEXT,
  "parentGenerationId" TEXT,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "provider" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "AudioPipelineJob_userId_createdAt_idx" ON "AudioPipelineJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AudioPipelineJob_status_idx" ON "AudioPipelineJob"("status");
CREATE INDEX IF NOT EXISTS "AudioPipelineJob_backendJobId_idx" ON "AudioPipelineJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "AudioPipelineJob_parentGenerationId_idx" ON "AudioPipelineJob"("parentGenerationId");
CREATE INDEX IF NOT EXISTS "AudioPipelineJob_engineVersion_idx" ON "AudioPipelineJob"("engineVersion");

CREATE TABLE IF NOT EXISTS "AudioQualityReportRecord" (
  "id" TEXT PRIMARY KEY,
  "audioPipelineJobId" TEXT,
  "voiceQuality" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "musicQuality" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "audioSynchronization" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "loudnessLufs" DOUBLE PRECISION NOT NULL DEFAULT -14,
  "dynamicRange" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "noiseScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "clippingScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "timelineAccuracy" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "subtitleAccuracy" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "localizationAccuracy" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "overallScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "passed" BOOLEAN NOT NULL DEFAULT false,
  "details" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioQualityReportRecord_audioPipelineJobId_idx" ON "AudioQualityReportRecord"("audioPipelineJobId");
CREATE INDEX IF NOT EXISTS "AudioQualityReportRecord_overallScore_idx" ON "AudioQualityReportRecord"("overallScore");

CREATE TABLE IF NOT EXISTS "AudioPipelineStageRecord" (
  "id" TEXT PRIMARY KEY,
  "audioPipelineJobId" TEXT,
  "stage" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "stageJobId" TEXT,
  "durationMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "summary" JSONB,
  "errorMessage" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioPipelineStageRecord_audioPipelineJobId_idx" ON "AudioPipelineStageRecord"("audioPipelineJobId");
CREATE INDEX IF NOT EXISTS "AudioPipelineStageRecord_stage_idx" ON "AudioPipelineStageRecord"("stage");

CREATE TABLE IF NOT EXISTS "AudioPipelineHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "audioPipelineJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioPipelineHistoryEntry_audioPipelineJobId_createdAt_idx" ON "AudioPipelineHistoryEntry"("audioPipelineJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "AudioPipelineMetricsRecord" (
  "id" TEXT PRIMARY KEY,
  "audioPipelineJobId" TEXT,
  "totalProcessingMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "queueTimeMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "exportTimeMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "downloadTimeMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "memoryMbEstimate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "cpuPercentEstimate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "gpuPercentEstimate" DOUBLE PRECISION,
  "successRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "details" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioPipelineMetricsRecord_audioPipelineJobId_idx" ON "AudioPipelineMetricsRecord"("audioPipelineJobId");
