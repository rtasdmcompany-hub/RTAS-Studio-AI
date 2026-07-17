-- Phase 5 Sprint 5 — AI Character Motion & Cinematic Animation Engine (UP)

CREATE TABLE IF NOT EXISTS "CharacterMotionJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "characterId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "emotion" TEXT,
  "durationSec" DOUBLE PRECISION,
  "actionsJson" JSONB,
  "profileJson" JSONB,
  "consistencyScore" DOUBLE PRECISION,
  "consistent" BOOLEAN NOT NULL DEFAULT false,
  "noBodyDistortion" BOOLEAN NOT NULL DEFAULT true,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "version" INTEGER NOT NULL DEFAULT 1,
  "integrationsJson" JSONB,
  "metadata" JSONB,
  "error" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CharacterMotionJob_characterId_idx" ON "CharacterMotionJob"("characterId");
CREATE INDEX IF NOT EXISTS "CharacterMotionJob_backendJobId_idx" ON "CharacterMotionJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "CharacterMotionJob_status_idx" ON "CharacterMotionJob"("status");
CREATE INDEX IF NOT EXISTS "CharacterMotionJob_createdAt_idx" ON "CharacterMotionJob"("createdAt" DESC);

CREATE TABLE IF NOT EXISTS "CharacterMotionClipRecord" (
  "id" TEXT PRIMARY KEY,
  "characterMotionJobId" TEXT,
  "clipId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "emotion" TEXT,
  "durationSec" DOUBLE PRECISION,
  "posesJson" JSONB,
  "locomotionJson" JSONB,
  "gesturesJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CharacterMotionClipRecord_clipId_idx" ON "CharacterMotionClipRecord"("clipId");
CREATE INDEX IF NOT EXISTS "CharacterMotionClipRecord_action_idx" ON "CharacterMotionClipRecord"("action");
CREATE INDEX IF NOT EXISTS "CharacterMotionClipRecord_characterMotionJobId_idx" ON "CharacterMotionClipRecord"("characterMotionJobId");

CREATE TABLE IF NOT EXISTS "CharacterMotionTimelineRecord" (
  "id" TEXT PRIMARY KEY,
  "characterMotionJobId" TEXT,
  "eventId" TEXT NOT NULL,
  "startSec" DOUBLE PRECISION NOT NULL,
  "endSec" DOUBLE PRECISION NOT NULL,
  "action" TEXT NOT NULL,
  "clipId" TEXT NOT NULL,
  "layer" TEXT NOT NULL DEFAULT 'body',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CharacterMotionTimelineRecord_eventId_idx" ON "CharacterMotionTimelineRecord"("eventId");
CREATE INDEX IF NOT EXISTS "CharacterMotionTimelineRecord_characterMotionJobId_idx" ON "CharacterMotionTimelineRecord"("characterMotionJobId");

CREATE TABLE IF NOT EXISTS "CharacterMotionProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "characterMotionJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "faceIdentityRef" TEXT,
  "bodyShape" TEXT,
  "height" TEXT,
  "weight" TEXT,
  "bodyProportions" TEXT,
  "walkingStyle" TEXT,
  "runningStyle" TEXT,
  "gestureStyle" TEXT,
  "eyeContact" TEXT,
  "headMovement" TEXT,
  "dnaFingerprint" TEXT,
  "profileJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CharacterMotionProfileRecord_characterId_idx" ON "CharacterMotionProfileRecord"("characterId");
CREATE INDEX IF NOT EXISTS "CharacterMotionProfileRecord_faceIdentityRef_idx" ON "CharacterMotionProfileRecord"("faceIdentityRef");
CREATE INDEX IF NOT EXISTS "CharacterMotionProfileRecord_characterMotionJobId_idx" ON "CharacterMotionProfileRecord"("characterMotionJobId");

CREATE TABLE IF NOT EXISTS "MotionLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "entryType" TEXT NOT NULL,
  "entryKey" TEXT NOT NULL,
  "category" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE ("entryType", "entryKey")
);
CREATE INDEX IF NOT EXISTS "MotionLibraryEntry_entryType_idx" ON "MotionLibraryEntry"("entryType");
CREATE INDEX IF NOT EXISTS "MotionLibraryEntry_category_idx" ON "MotionLibraryEntry"("category");

CREATE TABLE IF NOT EXISTS "PoseLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "poseId" TEXT NOT NULL UNIQUE,
  "name" TEXT,
  "jointsJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PoseLibraryEntry_poseId_idx" ON "PoseLibraryEntry"("poseId");

CREATE TABLE IF NOT EXISTS "GestureLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "gestureId" TEXT NOT NULL UNIQUE,
  "name" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "GestureLibraryEntry_gestureId_idx" ON "GestureLibraryEntry"("gestureId");

CREATE TABLE IF NOT EXISTS "AnimationMetadataRecord" (
  "id" TEXT PRIMARY KEY,
  "characterMotionJobId" TEXT,
  "characterId" TEXT,
  "animationDurationSec" DOUBLE PRECISION,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "errorsJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AnimationMetadataRecord_characterId_idx" ON "AnimationMetadataRecord"("characterId");
CREATE INDEX IF NOT EXISTS "AnimationMetadataRecord_characterMotionJobId_idx" ON "AnimationMetadataRecord"("characterMotionJobId");
