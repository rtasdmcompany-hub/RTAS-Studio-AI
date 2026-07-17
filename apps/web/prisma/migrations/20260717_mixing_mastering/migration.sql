-- Phase 4 Sprint 6 — Mixing & Mastering Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "AudioMixJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "kind" TEXT NOT NULL DEFAULT 'mix_master',
  "mixJobId" TEXT,
  "masterJobId" TEXT,
  "targetLufs" DOUBLE PRECISION NOT NULL DEFAULT -14,
  "truePeakCeiling" DOUBLE PRECISION NOT NULL DEFAULT -1,
  "integratedLufs" DOUBLE PRECISION,
  "truePeakDbtp" DOUBLE PRECISION,
  "qualityScore" DOUBLE PRECISION,
  "qualityGrade" TEXT,
  "clarityScore" DOUBLE PRECISION,
  "stereoWidth" DOUBLE PRECISION,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "assetUrl" TEXT,
  "masterUrl" TEXT,
  "exportFormat" TEXT NOT NULL DEFAULT 'wav',
  "exportSampleRate" INTEGER NOT NULL DEFAULT 48000,
  "exportBitDepth" INTEGER NOT NULL DEFAULT 24,
  "provider" TEXT,
  "audioVersion" INTEGER NOT NULL DEFAULT 1,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "parentVoiceJobId" TEXT,
  "parentMusicJobId" TEXT,
  "parentSfxJobId" TEXT,
  "parentAudioJobId" TEXT,
  "parentVideoJobId" TEXT,
  "parentGenerationId" TEXT,
  "mixProfile" JSONB,
  "masterProfile" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "AudioMixJob_userId_createdAt_idx" ON "AudioMixJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AudioMixJob_status_idx" ON "AudioMixJob"("status");
CREATE INDEX IF NOT EXISTS "AudioMixJob_kind_idx" ON "AudioMixJob"("kind");
CREATE INDEX IF NOT EXISTS "AudioMixJob_backendJobId_idx" ON "AudioMixJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "AudioMixJob_mixJobId_idx" ON "AudioMixJob"("mixJobId");
CREATE INDEX IF NOT EXISTS "AudioMixJob_masterJobId_idx" ON "AudioMixJob"("masterJobId");

CREATE TABLE IF NOT EXISTS "MasteringJob" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "backendMasterId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "targetLufs" DOUBLE PRECISION NOT NULL DEFAULT -14,
  "truePeakCeiling" DOUBLE PRECISION NOT NULL DEFAULT -1,
  "masterUrl" TEXT,
  "qualityScore" DOUBLE PRECISION,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "MasteringJob_audioMixJobId_idx" ON "MasteringJob"("audioMixJobId");
CREATE INDEX IF NOT EXISTS "MasteringJob_backendMasterId_idx" ON "MasteringJob"("backendMasterId");

CREATE TABLE IF NOT EXISTS "MixProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "dialoguePriority" BOOLEAN NOT NULL DEFAULT true,
  "musicDuckingDb" DOUBLE PRECISION NOT NULL DEFAULT -8,
  "sfxBalance" DOUBLE PRECISION NOT NULL DEFAULT 0.75,
  "ambientLevel" DOUBLE PRECISION NOT NULL DEFAULT 0.45,
  "compressionRatio" DOUBLE PRECISION NOT NULL DEFAULT 3,
  "profile" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MixProfileRecord_audioMixJobId_idx" ON "MixProfileRecord"("audioMixJobId");

CREATE TABLE IF NOT EXISTS "MasterProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "targetLufs" DOUBLE PRECISION NOT NULL DEFAULT -14,
  "truePeakCeilingDbtp" DOUBLE PRECISION NOT NULL DEFAULT -1,
  "stereoWidth" DOUBLE PRECISION NOT NULL DEFAULT 1.15,
  "noiseReduction" BOOLEAN NOT NULL DEFAULT true,
  "profile" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MasterProfileRecord_audioMixJobId_idx" ON "MasterProfileRecord"("audioMixJobId");

CREATE TABLE IF NOT EXISTS "LoudnessReport" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "integratedLufs" DOUBLE PRECISION NOT NULL,
  "shortTermLufs" DOUBLE PRECISION,
  "momentaryLufs" DOUBLE PRECISION,
  "truePeakDbtp" DOUBLE PRECISION,
  "peakDbfs" DOUBLE PRECISION,
  "loudnessRangeLu" DOUBLE PRECISION,
  "normalized" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LoudnessReport_audioMixJobId_idx" ON "LoudnessReport"("audioMixJobId");

CREATE TABLE IF NOT EXISTS "FrequencyAnalysis" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "lowEnergy" DOUBLE PRECISION,
  "midEnergy" DOUBLE PRECISION,
  "highEnergy" DOUBLE PRECISION,
  "spectralCentroidHz" DOUBLE PRECISION,
  "tonalBalanceScore" DOUBLE PRECISION,
  "bands" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "FrequencyAnalysis_audioMixJobId_idx" ON "FrequencyAnalysis"("audioMixJobId");

CREATE TABLE IF NOT EXISTS "AudioQualityReport" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "lufs" DOUBLE PRECISION,
  "peakDbfs" DOUBLE PRECISION,
  "truePeakDbtp" DOUBLE PRECISION,
  "dynamicRangeDb" DOUBLE PRECISION,
  "stereoWidth" DOUBLE PRECISION,
  "noiseFloorDb" DOUBLE PRECISION,
  "frequencyBalance" DOUBLE PRECISION,
  "clarityScore" DOUBLE PRECISION,
  "overallScore" DOUBLE PRECISION,
  "grade" TEXT,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "notes" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioQualityReport_audioMixJobId_idx" ON "AudioQualityReport"("audioMixJobId");
CREATE INDEX IF NOT EXISTS "AudioQualityReport_overallScore_idx" ON "AudioQualityReport"("overallScore");

CREATE TABLE IF NOT EXISTS "MixExportMetadata" (
  "id" TEXT PRIMARY KEY,
  "audioMixJobId" TEXT,
  "format" TEXT NOT NULL DEFAULT 'wav',
  "sampleRate" INTEGER NOT NULL DEFAULT 48000,
  "bitDepth" INTEGER NOT NULL DEFAULT 24,
  "masterUrl" TEXT,
  "assetUrl" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MixExportMetadata_audioMixJobId_idx" ON "MixExportMetadata"("audioMixJobId");
