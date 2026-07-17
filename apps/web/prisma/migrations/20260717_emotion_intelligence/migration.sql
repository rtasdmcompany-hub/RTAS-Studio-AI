-- Phase 5 Sprint 7 — AI Emotion, Expression & Performance Engine (UP)

CREATE TABLE IF NOT EXISTS "EmotionIntelligenceJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "characterId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "primaryEmotion" TEXT,
  "expressionScore" DOUBLE PRECISION,
  "performanceIntensity" DOUBLE PRECISION,
  "durationSec" DOUBLE PRECISION,
  "consistent" BOOLEAN NOT NULL DEFAULT false,
  "identityPreserved" BOOLEAN NOT NULL DEFAULT true,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "version" INTEGER NOT NULL DEFAULT 1,
  "analysisJson" JSONB,
  "expressionJson" JSONB,
  "performanceJson" JSONB,
  "integrationsJson" JSONB,
  "metadata" JSONB,
  "error" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EmotionIntelligenceJob_characterId_idx" ON "EmotionIntelligenceJob"("characterId");
CREATE INDEX IF NOT EXISTS "EmotionIntelligenceJob_backendJobId_idx" ON "EmotionIntelligenceJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "EmotionIntelligenceJob_status_idx" ON "EmotionIntelligenceJob"("status");
CREATE INDEX IF NOT EXISTS "EmotionIntelligenceJob_primaryEmotion_idx" ON "EmotionIntelligenceJob"("primaryEmotion");
CREATE INDEX IF NOT EXISTS "EmotionIntelligenceJob_createdAt_idx" ON "EmotionIntelligenceJob"("createdAt" DESC);

CREATE TABLE IF NOT EXISTS "EmotionProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "emotionIntelligenceJobId" TEXT,
  "characterId" TEXT,
  "primaryEmotion" TEXT NOT NULL,
  "secondaryEmotion" TEXT,
  "intensity" DOUBLE PRECISION,
  "faceEmbeddingRef" TEXT,
  "dnaFingerprint" TEXT,
  "memoryKey" TEXT,
  "profileJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EmotionProfileRecord_characterId_idx" ON "EmotionProfileRecord"("characterId");
CREATE INDEX IF NOT EXISTS "EmotionProfileRecord_primaryEmotion_idx" ON "EmotionProfileRecord"("primaryEmotion");
CREATE INDEX IF NOT EXISTS "EmotionProfileRecord_emotionIntelligenceJobId_idx" ON "EmotionProfileRecord"("emotionIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "ExpressionLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "expressionId" TEXT NOT NULL UNIQUE,
  "region" TEXT,
  "intensity" DOUBLE PRECISION,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ExpressionLibraryEntry_expressionId_idx" ON "ExpressionLibraryEntry"("expressionId");
CREATE INDEX IF NOT EXISTS "ExpressionLibraryEntry_region_idx" ON "ExpressionLibraryEntry"("region");

CREATE TABLE IF NOT EXISTS "PerformanceLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "performanceId" TEXT NOT NULL UNIQUE,
  "category" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PerformanceLibraryEntry_performanceId_idx" ON "PerformanceLibraryEntry"("performanceId");
CREATE INDEX IF NOT EXISTS "PerformanceLibraryEntry_category_idx" ON "PerformanceLibraryEntry"("category");

CREATE TABLE IF NOT EXISTS "EmotionTimelineRecord" (
  "id" TEXT PRIMARY KEY,
  "emotionIntelligenceJobId" TEXT,
  "eventId" TEXT NOT NULL,
  "startSec" DOUBLE PRECISION NOT NULL,
  "endSec" DOUBLE PRECISION NOT NULL,
  "emotion" TEXT NOT NULL,
  "intensity" DOUBLE PRECISION,
  "expressionId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EmotionTimelineRecord_eventId_idx" ON "EmotionTimelineRecord"("eventId");
CREATE INDEX IF NOT EXISTS "EmotionTimelineRecord_emotion_idx" ON "EmotionTimelineRecord"("emotion");
CREATE INDEX IF NOT EXISTS "EmotionTimelineRecord_emotionIntelligenceJobId_idx" ON "EmotionTimelineRecord"("emotionIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "CharacterEmotionHistory" (
  "id" TEXT PRIMARY KEY,
  "emotionIntelligenceJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "emotion" TEXT NOT NULL,
  "intensity" DOUBLE PRECISION,
  "expressionScore" DOUBLE PRECISION,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CharacterEmotionHistory_characterId_createdAt_idx" ON "CharacterEmotionHistory"("characterId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CharacterEmotionHistory_emotion_idx" ON "CharacterEmotionHistory"("emotion");
CREATE INDEX IF NOT EXISTS "CharacterEmotionHistory_emotionIntelligenceJobId_idx" ON "CharacterEmotionHistory"("emotionIntelligenceJobId");

CREATE TABLE IF NOT EXISTS "EmotionMetadataRecord" (
  "id" TEXT PRIMARY KEY,
  "emotionIntelligenceJobId" TEXT,
  "characterId" TEXT,
  "emotionType" TEXT,
  "expressionScore" DOUBLE PRECISION,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "errorsJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EmotionMetadataRecord_characterId_idx" ON "EmotionMetadataRecord"("characterId");
CREATE INDEX IF NOT EXISTS "EmotionMetadataRecord_emotionType_idx" ON "EmotionMetadataRecord"("emotionType");
CREATE INDEX IF NOT EXISTS "EmotionMetadataRecord_emotionIntelligenceJobId_idx" ON "EmotionMetadataRecord"("emotionIntelligenceJobId");
