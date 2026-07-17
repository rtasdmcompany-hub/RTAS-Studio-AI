-- Phase 4 Sprint 8 — Audio Timeline & Cinematic Synchronization (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "TimelineJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "fps" DOUBLE PRECISION NOT NULL DEFAULT 24,
  "durationSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "trackCount" INTEGER NOT NULL DEFAULT 0,
  "sceneCount" INTEGER NOT NULL DEFAULT 0,
  "shotCount" INTEGER NOT NULL DEFAULT 0,
  "beatCount" INTEGER NOT NULL DEFAULT 0,
  "syncAccuracy" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "locked" BOOLEAN NOT NULL DEFAULT false,
  "snapEnabled" BOOLEAN NOT NULL DEFAULT true,
  "autoAlign" BOOLEAN NOT NULL DEFAULT true,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "exportUrl" TEXT,
  "masterTimelineUrl" TEXT,
  "provider" TEXT,
  "timelineVersion" INTEGER NOT NULL DEFAULT 1,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "parentVoiceJobId" TEXT,
  "parentMusicJobId" TEXT,
  "parentSfxJobId" TEXT,
  "parentMixJobId" TEXT,
  "parentLocalizationJobId" TEXT,
  "parentVideoJobId" TEXT,
  "parentGenerationId" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "TimelineJob_userId_createdAt_idx" ON "TimelineJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "TimelineJob_status_idx" ON "TimelineJob"("status");
CREATE INDEX IF NOT EXISTS "TimelineJob_backendJobId_idx" ON "TimelineJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "TimelineJob_parentGenerationId_idx" ON "TimelineJob"("parentGenerationId");

CREATE TABLE IF NOT EXISTS "TimelineTrackRecord" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "trackId" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "name" TEXT,
  "gainDb" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "muted" BOOLEAN NOT NULL DEFAULT false,
  "locked" BOOLEAN NOT NULL DEFAULT false,
  "snapEnabled" BOOLEAN NOT NULL DEFAULT true,
  "sortOrder" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TimelineTrackRecord_timelineJobId_idx" ON "TimelineTrackRecord"("timelineJobId");
CREATE INDEX IF NOT EXISTS "TimelineTrackRecord_trackId_idx" ON "TimelineTrackRecord"("trackId");
CREATE INDEX IF NOT EXISTS "TimelineTrackRecord_kind_idx" ON "TimelineTrackRecord"("kind");

CREATE TABLE IF NOT EXISTS "TimelineEventRecord" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "eventId" TEXT NOT NULL,
  "trackId" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "startSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "endSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "label" TEXT,
  "sceneId" TEXT,
  "shotId" TEXT,
  "frame" INTEGER,
  "emotion" TEXT,
  "assetUrl" TEXT,
  "gainDb" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "locked" BOOLEAN NOT NULL DEFAULT false,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TimelineEventRecord_timelineJobId_idx" ON "TimelineEventRecord"("timelineJobId");
CREATE INDEX IF NOT EXISTS "TimelineEventRecord_trackId_idx" ON "TimelineEventRecord"("trackId");
CREATE INDEX IF NOT EXISTS "TimelineEventRecord_sceneId_idx" ON "TimelineEventRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "TimelineEventRecord_shotId_idx" ON "TimelineEventRecord"("shotId");

CREATE TABLE IF NOT EXISTS "AudioLayerRecord" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "layerId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "trackIds" JSONB,
  "blendMode" TEXT NOT NULL DEFAULT 'mix',
  "gainDb" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "enabled" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AudioLayerRecord_timelineJobId_idx" ON "AudioLayerRecord"("timelineJobId");
CREATE INDEX IF NOT EXISTS "AudioLayerRecord_layerId_idx" ON "AudioLayerRecord"("layerId");

CREATE TABLE IF NOT EXISTS "SyncMetadataRecord" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "mode" TEXT NOT NULL DEFAULT 'auto',
  "fps" DOUBLE PRECISION NOT NULL DEFAULT 24,
  "frameAccuracyMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "syncAccuracy" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "sceneCount" INTEGER NOT NULL DEFAULT 0,
  "shotCount" INTEGER NOT NULL DEFAULT 0,
  "beatCount" INTEGER NOT NULL DEFAULT 0,
  "lipSyncAligned" BOOLEAN NOT NULL DEFAULT false,
  "emotionAligned" BOOLEAN NOT NULL DEFAULT false,
  "cameraMusicAligned" BOOLEAN NOT NULL DEFAULT false,
  "dynamicBalance" BOOLEAN NOT NULL DEFAULT true,
  "snapGridMs" DOUBLE PRECISION NOT NULL DEFAULT 33.33,
  "details" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SyncMetadataRecord_timelineJobId_idx" ON "SyncMetadataRecord"("timelineJobId");

CREATE TABLE IF NOT EXISTS "BeatMarkerRecord" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "markerId" TEXT NOT NULL,
  "timeSec" DOUBLE PRECISION NOT NULL,
  "beatIndex" INTEGER NOT NULL DEFAULT 0,
  "intensity" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "bar" INTEGER,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "BeatMarkerRecord_timelineJobId_idx" ON "BeatMarkerRecord"("timelineJobId");
CREATE INDEX IF NOT EXISTS "BeatMarkerRecord_timeSec_idx" ON "BeatMarkerRecord"("timeSec");

CREATE TABLE IF NOT EXISTS "TimelineHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TimelineHistoryEntry_timelineJobId_createdAt_idx" ON "TimelineHistoryEntry"("timelineJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "TimelineVersionRecord" (
  "id" TEXT PRIMARY KEY,
  "timelineJobId" TEXT,
  "version" INTEGER NOT NULL,
  "label" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TimelineVersionRecord_timelineJobId_version_idx" ON "TimelineVersionRecord"("timelineJobId", "version");
