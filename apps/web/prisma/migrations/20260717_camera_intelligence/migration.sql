-- Phase 5 Sprint 6 — AI Cinematic Camera & Shot Intelligence Engine (UP)

CREATE TABLE IF NOT EXISTS "CameraIntelligenceJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "sceneId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "promptPreview" TEXT,
  "durationSec" DOUBLE PRECISION,
  "shotCount" INTEGER NOT NULL DEFAULT 0,
  "primaryShotType" TEXT,
  "primaryLens" TEXT,
  "coverageScore" DOUBLE PRECISION,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "version" INTEGER NOT NULL DEFAULT 1,
  "analysisJson" JSONB,
  "integrationsJson" JSONB,
  "metadata" JSONB,
  "error" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CameraIntelligenceJob_backendJobId_idx" ON "CameraIntelligenceJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "CameraIntelligenceJob_sceneId_idx" ON "CameraIntelligenceJob"("sceneId");
CREATE INDEX IF NOT EXISTS "CameraIntelligenceJob_status_idx" ON "CameraIntelligenceJob"("status");
CREATE INDEX IF NOT EXISTS "CameraIntelligenceJob_createdAt_idx" ON "CameraIntelligenceJob"("createdAt" DESC);

CREATE TABLE IF NOT EXISTS "CameraShotRecord" (
  "id" TEXT PRIMARY KEY,
  "cameraIntelligenceJobId" TEXT,
  "shotId" TEXT NOT NULL,
  "shotType" TEXT NOT NULL,
  "lensId" TEXT,
  "focalLengthMm" DOUBLE PRECISION,
  "durationSec" DOUBLE PRECISION,
  "startSec" DOUBLE PRECISION,
  "endSec" DOUBLE PRECISION,
  "framingJson" JSONB,
  "compositionJson" JSONB,
  "motionJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CameraShotRecord_shotId_idx" ON "CameraShotRecord"("shotId");
CREATE INDEX IF NOT EXISTS "CameraShotRecord_shotType_idx" ON "CameraShotRecord"("shotType");
CREATE INDEX IF NOT EXISTS "CameraShotRecord_cameraIntelligenceJobId_idx" ON "CameraShotRecord"("cameraIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "CameraTimelineRecord" (
  "id" TEXT PRIMARY KEY,
  "cameraIntelligenceJobId" TEXT,
  "eventId" TEXT NOT NULL,
  "startSec" DOUBLE PRECISION NOT NULL,
  "endSec" DOUBLE PRECISION NOT NULL,
  "shotId" TEXT NOT NULL,
  "shotType" TEXT NOT NULL,
  "layer" TEXT NOT NULL DEFAULT 'camera',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CameraTimelineRecord_eventId_idx" ON "CameraTimelineRecord"("eventId");
CREATE INDEX IF NOT EXISTS "CameraTimelineRecord_cameraIntelligenceJobId_idx" ON "CameraTimelineRecord"("cameraIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "ShotLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "shotId" TEXT NOT NULL UNIQUE,
  "category" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ShotLibraryEntry_category_idx" ON "ShotLibraryEntry"("category");

CREATE TABLE IF NOT EXISTS "LensLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "lensId" TEXT NOT NULL UNIQUE,
  "name" TEXT,
  "focalLengthMm" DOUBLE PRECISION,
  "aperture" DOUBLE PRECISION,
  "depthOfField" TEXT,
  "useCase" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LensLibraryEntry_lensId_idx" ON "LensLibraryEntry"("lensId");

CREATE TABLE IF NOT EXISTS "CameraPresetEntry" (
  "id" TEXT PRIMARY KEY,
  "presetId" TEXT NOT NULL UNIQUE,
  "name" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CameraPresetEntry_presetId_idx" ON "CameraPresetEntry"("presetId");

CREATE TABLE IF NOT EXISTS "CompositionProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "cameraIntelligenceJobId" TEXT,
  "sceneId" TEXT,
  "ruleOfThirds" BOOLEAN NOT NULL DEFAULT true,
  "leadRoom" BOOLEAN NOT NULL DEFAULT true,
  "headroom" BOOLEAN NOT NULL DEFAULT true,
  "profileJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CompositionProfileRecord_sceneId_idx" ON "CompositionProfileRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "CompositionProfileRecord_cameraIntelligenceJobId_idx" ON "CompositionProfileRecord"("cameraIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "ShotMetadataRecord" (
  "id" TEXT PRIMARY KEY,
  "cameraIntelligenceJobId" TEXT,
  "shotType" TEXT,
  "lensUsed" TEXT,
  "sceneId" TEXT,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "errorsJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ShotMetadataRecord_sceneId_idx" ON "ShotMetadataRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "ShotMetadataRecord_shotType_idx" ON "ShotMetadataRecord"("shotType");
CREATE INDEX IF NOT EXISTS "ShotMetadataRecord_cameraIntelligenceJobId_idx" ON "ShotMetadataRecord"("cameraIntelligenceJobId");
