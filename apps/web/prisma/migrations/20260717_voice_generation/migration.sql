-- Phase 4 Sprint 2 — Voice Generation Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "VoiceJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "audioJobId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "text" TEXT NOT NULL,
  "language" TEXT NOT NULL DEFAULT 'en',
  "voiceId" TEXT NOT NULL,
  "gender" TEXT,
  "provider" TEXT,
  "voiceModel" TEXT,
  "speed" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "pitch" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "volume" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "pauseMs" INTEGER NOT NULL DEFAULT 0,
  "ssml" TEXT,
  "estimatedDurationSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "qualityScore" DOUBLE PRECISION,
  "qualityGrade" TEXT,
  "assetUrl" TEXT,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "exportReady" BOOLEAN NOT NULL DEFAULT false,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "version" INTEGER NOT NULL DEFAULT 1,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);

CREATE INDEX IF NOT EXISTS "VoiceJob_userId_createdAt_idx" ON "VoiceJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "VoiceJob_status_idx" ON "VoiceJob"("status");
CREATE INDEX IF NOT EXISTS "VoiceJob_language_idx" ON "VoiceJob"("language");
CREATE INDEX IF NOT EXISTS "VoiceJob_backendJobId_idx" ON "VoiceJob"("backendJobId");

CREATE TABLE IF NOT EXISTS "VoiceProfile" (
  "id" TEXT PRIMARY KEY,
  "voiceJobId" TEXT,
  "voiceId" TEXT NOT NULL,
  "name" TEXT,
  "language" TEXT NOT NULL,
  "gender" TEXT,
  "style" TEXT,
  "providerModel" TEXT,
  "sampleRate" INTEGER NOT NULL DEFAULT 24000,
  "tags" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceProfile_voiceId_idx" ON "VoiceProfile"("voiceId");
CREATE INDEX IF NOT EXISTS "VoiceProfile_language_idx" ON "VoiceProfile"("language");
CREATE INDEX IF NOT EXISTS "VoiceProfile_voiceJobId_idx" ON "VoiceProfile"("voiceJobId");

CREATE TABLE IF NOT EXISTS "VoiceSynthAsset" (
  "id" TEXT PRIMARY KEY,
  "voiceJobId" TEXT,
  "format" TEXT NOT NULL DEFAULT 'wav',
  "assetUrl" TEXT,
  "filename" TEXT,
  "bytes" INTEGER,
  "checksum" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceSynthAsset_voiceJobId_idx" ON "VoiceSynthAsset"("voiceJobId");

CREATE TABLE IF NOT EXISTS "VoiceMeta" (
  "id" TEXT PRIMARY KEY,
  "voiceJobId" TEXT,
  "key" TEXT NOT NULL,
  "value" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceMeta_voiceJobId_key_idx" ON "VoiceMeta"("voiceJobId", "key");

CREATE TABLE IF NOT EXISTS "VoiceHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "voiceJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceHistoryEntry_voiceJobId_createdAt_idx" ON "VoiceHistoryEntry"("voiceJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "VoiceVersion" (
  "id" TEXT PRIMARY KEY,
  "voiceJobId" TEXT,
  "version" INTEGER NOT NULL,
  "ssml" TEXT,
  "assetUrl" TEXT,
  "qualityScore" DOUBLE PRECISION,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceVersion_voiceJobId_version_idx" ON "VoiceVersion"("voiceJobId", "version");
