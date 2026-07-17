-- Phase 4 Sprint 3 — Voice Cloning & Character Voice Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "VoiceClone" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendCloneId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "characterId" TEXT,
  "referenceUrl" TEXT NOT NULL,
  "referenceChecksum" TEXT,
  "language" TEXT NOT NULL DEFAULT 'en',
  "accent" TEXT NOT NULL DEFAULT 'neutral',
  "speakingStyle" TEXT NOT NULL DEFAULT 'natural',
  "emotionProfile" TEXT NOT NULL DEFAULT 'calm',
  "gender" TEXT,
  "ageGroup" TEXT,
  "voiceLocked" BOOLEAN NOT NULL DEFAULT false,
  "voiceVersion" INTEGER NOT NULL DEFAULT 1,
  "provider" TEXT,
  "qualityScore" DOUBLE PRECISION,
  "qualityGrade" TEXT,
  "speakerVerified" BOOLEAN NOT NULL DEFAULT false,
  "previewUrl" TEXT,
  "assetUrl" TEXT,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "trainingDurationMs" DOUBLE PRECISION,
  "processingTimeMs" DOUBLE PRECISION,
  "parentGenerationId" TEXT,
  "parentVideoJobId" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "VoiceClone_userId_createdAt_idx" ON "VoiceClone"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "VoiceClone_status_idx" ON "VoiceClone"("status");
CREATE INDEX IF NOT EXISTS "VoiceClone_characterId_idx" ON "VoiceClone"("characterId");
CREATE INDEX IF NOT EXISTS "VoiceClone_backendCloneId_idx" ON "VoiceClone"("backendCloneId");

CREATE TABLE IF NOT EXISTS "CharacterVoice" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "characterId" TEXT NOT NULL UNIQUE,
  "voiceCloneId" TEXT,
  "defaultVoice" TEXT NOT NULL,
  "language" TEXT NOT NULL DEFAULT 'en',
  "accent" TEXT NOT NULL DEFAULT 'neutral',
  "speakingStyle" TEXT NOT NULL DEFAULT 'natural',
  "emotionProfile" TEXT NOT NULL DEFAULT 'calm',
  "gender" TEXT,
  "ageGroup" TEXT,
  "voiceVersion" INTEGER NOT NULL DEFAULT 1,
  "voiceLocked" BOOLEAN NOT NULL DEFAULT false,
  "speakerId" TEXT,
  "previewUrl" TEXT,
  "voiceMetadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CharacterVoice_userId_idx" ON "CharacterVoice"("userId");
CREATE INDEX IF NOT EXISTS "CharacterVoice_voiceCloneId_idx" ON "CharacterVoice"("voiceCloneId");
CREATE INDEX IF NOT EXISTS "CharacterVoice_defaultVoice_idx" ON "CharacterVoice"("defaultVoice");

CREATE TABLE IF NOT EXISTS "SpeakerProfile" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "voiceCloneId" TEXT,
  "backendSpeakerId" TEXT UNIQUE,
  "gender" TEXT,
  "ageGroup" TEXT,
  "language" TEXT NOT NULL DEFAULT 'en',
  "accent" TEXT NOT NULL DEFAULT 'neutral',
  "speakingStyle" TEXT NOT NULL DEFAULT 'natural',
  "emotionProfile" TEXT NOT NULL DEFAULT 'calm',
  "locked" BOOLEAN NOT NULL DEFAULT false,
  "version" INTEGER NOT NULL DEFAULT 1,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SpeakerProfile_userId_idx" ON "SpeakerProfile"("userId");
CREATE INDEX IF NOT EXISTS "SpeakerProfile_voiceCloneId_idx" ON "SpeakerProfile"("voiceCloneId");
CREATE INDEX IF NOT EXISTS "SpeakerProfile_backendSpeakerId_idx" ON "SpeakerProfile"("backendSpeakerId");

CREATE TABLE IF NOT EXISTS "VoiceFingerprint" (
  "id" TEXT PRIMARY KEY,
  "voiceCloneId" TEXT,
  "speakerProfileId" TEXT,
  "fingerprintId" TEXT NOT NULL UNIQUE,
  "checksum" TEXT NOT NULL,
  "embeddingRef" TEXT,
  "sampleRate" INTEGER NOT NULL DEFAULT 24000,
  "durationSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "spectralHash" TEXT,
  "speakerScore" DOUBLE PRECISION,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceFingerprint_voiceCloneId_idx" ON "VoiceFingerprint"("voiceCloneId");
CREATE INDEX IF NOT EXISTS "VoiceFingerprint_checksum_idx" ON "VoiceFingerprint"("checksum");
CREATE INDEX IF NOT EXISTS "VoiceFingerprint_speakerProfileId_idx" ON "VoiceFingerprint"("speakerProfileId");

CREATE TABLE IF NOT EXISTS "VoiceCloneMeta" (
  "id" TEXT PRIMARY KEY,
  "voiceCloneId" TEXT,
  "key" TEXT NOT NULL,
  "value" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceCloneMeta_voiceCloneId_key_idx" ON "VoiceCloneMeta"("voiceCloneId", "key");

CREATE TABLE IF NOT EXISTS "VoiceCloneVersion" (
  "id" TEXT PRIMARY KEY,
  "voiceCloneId" TEXT,
  "version" INTEGER NOT NULL,
  "assetUrl" TEXT,
  "previewUrl" TEXT,
  "qualityScore" DOUBLE PRECISION,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceCloneVersion_voiceCloneId_version_idx" ON "VoiceCloneVersion"("voiceCloneId", "version");

CREATE TABLE IF NOT EXISTS "VoiceTrainingHistory" (
  "id" TEXT PRIMARY KEY,
  "voiceCloneId" TEXT,
  "version" INTEGER NOT NULL,
  "trainingDurationMs" DOUBLE PRECISION,
  "provider" TEXT,
  "qualityScore" DOUBLE PRECISION,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceTrainingHistory_voiceCloneId_createdAt_idx" ON "VoiceTrainingHistory"("voiceCloneId", "createdAt" DESC);
