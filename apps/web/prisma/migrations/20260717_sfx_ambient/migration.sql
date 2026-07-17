-- Phase 4 Sprint 5 — Sound Effects & Ambient Audio Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "SfxJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "kind" TEXT NOT NULL DEFAULT 'scene',
  "categories" JSONB,
  "environment" TEXT,
  "mood" TEXT,
  "energy" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "sceneId" TEXT,
  "durationSec" DOUBLE PRECISION NOT NULL DEFAULT 12,
  "volume" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "loop" BOOLEAN NOT NULL DEFAULT false,
  "fadeInSec" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "fadeOutSec" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "assetUrl" TEXT,
  "previewUrl" TEXT,
  "libraryIds" JSONB,
  "provider" TEXT,
  "audioVersion" INTEGER NOT NULL DEFAULT 1,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "parentAudioJobId" TEXT,
  "parentMusicJobId" TEXT,
  "parentVideoJobId" TEXT,
  "parentGenerationId" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "SfxJob_userId_createdAt_idx" ON "SfxJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "SfxJob_status_idx" ON "SfxJob"("status");
CREATE INDEX IF NOT EXISTS "SfxJob_kind_idx" ON "SfxJob"("kind");
CREATE INDEX IF NOT EXISTS "SfxJob_environment_idx" ON "SfxJob"("environment");
CREATE INDEX IF NOT EXISTS "SfxJob_backendJobId_idx" ON "SfxJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "SfxJob_sceneId_idx" ON "SfxJob"("sceneId");

CREATE TABLE IF NOT EXISTS "AmbientAsset" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "category" TEXT NOT NULL,
  "kind" TEXT NOT NULL DEFAULT 'ambient',
  "assetUrl" TEXT,
  "filename" TEXT,
  "durationSec" DOUBLE PRECISION,
  "loop" BOOLEAN NOT NULL DEFAULT true,
  "volume" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "checksum" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AmbientAsset_sfxJobId_idx" ON "AmbientAsset"("sfxJobId");
CREATE INDEX IF NOT EXISTS "AmbientAsset_category_idx" ON "AmbientAsset"("category");

CREATE TABLE IF NOT EXISTS "SfxLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "libraryId" TEXT NOT NULL UNIQUE,
  "category" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "environment" TEXT,
  "durationSec" DOUBLE PRECISION,
  "loop" BOOLEAN NOT NULL DEFAULT false,
  "volume" DOUBLE PRECISION,
  "assetUrl" TEXT,
  "audioVersion" INTEGER NOT NULL DEFAULT 1,
  "tags" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SfxLibraryEntry_category_idx" ON "SfxLibraryEntry"("category");
CREATE INDEX IF NOT EXISTS "SfxLibraryEntry_kind_idx" ON "SfxLibraryEntry"("kind");
CREATE INDEX IF NOT EXISTS "SfxLibraryEntry_sfxJobId_idx" ON "SfxLibraryEntry"("sfxJobId");

CREATE TABLE IF NOT EXISTS "EnvironmentProfile" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "environment" TEXT NOT NULL,
  "mood" TEXT,
  "energy" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "sceneId" TEXT,
  "recommendedCategories" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EnvironmentProfile_environment_idx" ON "EnvironmentProfile"("environment");
CREATE INDEX IF NOT EXISTS "EnvironmentProfile_sfxJobId_idx" ON "EnvironmentProfile"("sfxJobId");
CREATE INDEX IF NOT EXISTS "EnvironmentProfile_sceneId_idx" ON "EnvironmentProfile"("sceneId");

CREATE TABLE IF NOT EXISTS "AudioLayer" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "layerId" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "volume" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "startSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "endSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "loop" BOOLEAN NOT NULL DEFAULT false,
  "fadeInSec" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "fadeOutSec" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "spatial" JSONB,
  "assetUrl" TEXT,
  "libraryId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioLayer_sfxJobId_idx" ON "AudioLayer"("sfxJobId");
CREATE INDEX IF NOT EXISTS "AudioLayer_layerId_idx" ON "AudioLayer"("layerId");
CREATE INDEX IF NOT EXISTS "AudioLayer_category_idx" ON "AudioLayer"("category");

CREATE TABLE IF NOT EXISTS "SfxTimelineEvent" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "eventId" TEXT NOT NULL,
  "sceneId" TEXT,
  "atSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "category" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "layerId" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SfxTimelineEvent_sfxJobId_atSec_idx" ON "SfxTimelineEvent"("sfxJobId", "atSec");
CREATE INDEX IF NOT EXISTS "SfxTimelineEvent_sceneId_idx" ON "SfxTimelineEvent"("sceneId");
CREATE INDEX IF NOT EXISTS "SfxTimelineEvent_eventId_idx" ON "SfxTimelineEvent"("eventId");

CREATE TABLE IF NOT EXISTS "SfxAssetMeta" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "key" TEXT NOT NULL,
  "value" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SfxAssetMeta_sfxJobId_key_idx" ON "SfxAssetMeta"("sfxJobId", "key");

CREATE TABLE IF NOT EXISTS "SfxHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "sfxJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SfxHistoryEntry_sfxJobId_createdAt_idx" ON "SfxHistoryEntry"("sfxJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "SfxCategoryLibrary" (
  "id" TEXT PRIMARY KEY,
  "code" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL DEFAULT 'sfx',
  "defaultVolume" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "loopable" BOOLEAN NOT NULL DEFAULT false,
  "tags" JSONB,
  "moodAffinity" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SfxCategoryLibrary_kind_idx" ON "SfxCategoryLibrary"("kind");
CREATE INDEX IF NOT EXISTS "SfxCategoryLibrary_active_idx" ON "SfxCategoryLibrary"("active");
