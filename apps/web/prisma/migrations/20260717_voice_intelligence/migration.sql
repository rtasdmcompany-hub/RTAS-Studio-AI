-- Phase 5 Sprint 4 — AI Voice & Dialogue Intelligence Engine (UP)

CREATE TABLE IF NOT EXISTS "VoiceIntelligenceJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "projectId" TEXT NOT NULL,
  "jobId" TEXT NOT NULL,
  "language" TEXT NOT NULL DEFAULT 'en',
  "scriptPreview" TEXT,
  "lineCount" INTEGER NOT NULL DEFAULT 0,
  "voiceCount" INTEGER NOT NULL DEFAULT 0,
  "totalDurationSec" DOUBLE PRECISION,
  "consistencyScore" DOUBLE PRECISION,
  "consistent" BOOLEAN NOT NULL DEFAULT false,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "version" INTEGER NOT NULL DEFAULT 1,
  "payloadJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceIntelligenceJob_projectId_idx" ON "VoiceIntelligenceJob"("projectId");
CREATE INDEX IF NOT EXISTS "VoiceIntelligenceJob_jobId_idx" ON "VoiceIntelligenceJob"("jobId");
CREATE INDEX IF NOT EXISTS "VoiceIntelligenceJob_language_idx" ON "VoiceIntelligenceJob"("language");

CREATE TABLE IF NOT EXISTS "VoiceDialogueLineRecord" (
  "id" TEXT PRIMARY KEY,
  "voiceIntelligenceJobId" TEXT,
  "projectId" TEXT NOT NULL,
  "lineId" TEXT NOT NULL,
  "lineIndex" INTEGER NOT NULL,
  "role" TEXT NOT NULL,
  "emotion" TEXT NOT NULL,
  "voiceId" TEXT,
  "text" TEXT NOT NULL,
  "startSec" DOUBLE PRECISION,
  "endSec" DOUBLE PRECISION,
  "speakingDurationSec" DOUBLE PRECISION,
  "pauseAfterSec" DOUBLE PRECISION,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceDialogueLineRecord_projectId_idx" ON "VoiceDialogueLineRecord"("projectId");
CREATE INDEX IF NOT EXISTS "VoiceDialogueLineRecord_lineId_idx" ON "VoiceDialogueLineRecord"("lineId");
CREATE INDEX IF NOT EXISTS "VoiceDialogueLineRecord_role_idx" ON "VoiceDialogueLineRecord"("role");
CREATE INDEX IF NOT EXISTS "VoiceDialogueLineRecord_voiceIntelligenceJobId_idx" ON "VoiceDialogueLineRecord"("voiceIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "VoiceCharacterProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "voiceIntelligenceJobId" TEXT,
  "projectId" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "voiceId" TEXT NOT NULL,
  "gender" TEXT,
  "ageGroup" TEXT,
  "language" TEXT,
  "accent" TEXT,
  "speakingSpeed" DOUBLE PRECISION,
  "pitch" DOUBLE PRECISION,
  "energy" DOUBLE PRECISION,
  "emotionStyle" TEXT,
  "narrationStyle" TEXT,
  "characterSlot" TEXT,
  "profileJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceCharacterProfileRecord_projectId_idx" ON "VoiceCharacterProfileRecord"("projectId");
CREATE INDEX IF NOT EXISTS "VoiceCharacterProfileRecord_voiceId_idx" ON "VoiceCharacterProfileRecord"("voiceId");
CREATE INDEX IF NOT EXISTS "VoiceCharacterProfileRecord_role_idx" ON "VoiceCharacterProfileRecord"("role");
CREATE INDEX IF NOT EXISTS "VoiceCharacterProfileRecord_voiceIntelligenceJobId_idx" ON "VoiceCharacterProfileRecord"("voiceIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "VoiceConsistencyRecord" (
  "id" TEXT PRIMARY KEY,
  "voiceIntelligenceJobId" TEXT,
  "projectId" TEXT NOT NULL,
  "consistencyScore" DOUBLE PRECISION NOT NULL,
  "consistent" BOOLEAN NOT NULL DEFAULT false,
  "sameVoiceAcrossScenes" BOOLEAN NOT NULL DEFAULT true,
  "sameAccent" BOOLEAN NOT NULL DEFAULT true,
  "emotionContinuity" BOOLEAN NOT NULL DEFAULT true,
  "noUnexpectedSwitching" BOOLEAN NOT NULL DEFAULT true,
  "dialogueSynchronized" BOOLEAN NOT NULL DEFAULT true,
  "issues" JSONB,
  "notes" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "VoiceConsistencyRecord_projectId_createdAt_idx" ON "VoiceConsistencyRecord"("projectId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "VoiceConsistencyRecord_voiceIntelligenceJobId_idx" ON "VoiceConsistencyRecord"("voiceIntelligenceJobId");
