-- Phase 5 Sprint 1 — AI Avatar & Character Generation Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "AvatarCharacterJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "characterId" TEXT NOT NULL,
  "uniqueId" TEXT,
  "registrySlot" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "name" TEXT,
  "templateId" TEXT,
  "characterVersion" INTEGER NOT NULL DEFAULT 1,
  "gender" TEXT,
  "age" INTEGER,
  "ethnicity" TEXT,
  "bodyType" TEXT,
  "hairstyle" TEXT,
  "beard" TEXT,
  "skin" TEXT,
  "eyeColor" TEXT,
  "clothing" TEXT,
  "accessories" JSONB,
  "dnaFingerprint" TEXT,
  "dnaJson" JSONB,
  "previewUrl" TEXT,
  "dnaUrl" TEXT,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "paddleVerified" BOOLEAN NOT NULL DEFAULT false,
  "provider" TEXT,
  "parentGenerationId" TEXT,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "errorMessage" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "AvatarCharacterJob_userId_createdAt_idx" ON "AvatarCharacterJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AvatarCharacterJob_characterId_idx" ON "AvatarCharacterJob"("characterId");
CREATE INDEX IF NOT EXISTS "AvatarCharacterJob_registrySlot_idx" ON "AvatarCharacterJob"("registrySlot");
CREATE INDEX IF NOT EXISTS "AvatarCharacterJob_backendJobId_idx" ON "AvatarCharacterJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "AvatarCharacterJob_status_idx" ON "AvatarCharacterJob"("status");

CREATE TABLE IF NOT EXISTS "AvatarCharacterDNA" (
  "id" TEXT PRIMARY KEY,
  "avatarCharacterJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "dnaId" TEXT NOT NULL,
  "version" INTEGER NOT NULL DEFAULT 1,
  "fingerprint" TEXT,
  "locked" BOOLEAN NOT NULL DEFAULT true,
  "payload" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AvatarCharacterDNA_characterId_idx" ON "AvatarCharacterDNA"("characterId");
CREATE INDEX IF NOT EXISTS "AvatarCharacterDNA_dnaId_idx" ON "AvatarCharacterDNA"("dnaId");
CREATE INDEX IF NOT EXISTS "AvatarCharacterDNA_avatarCharacterJobId_idx" ON "AvatarCharacterDNA"("avatarCharacterJobId");

CREATE TABLE IF NOT EXISTS "AvatarCharacterHistory" (
  "id" TEXT PRIMARY KEY,
  "avatarCharacterJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AvatarCharacterHistory_avatarCharacterJobId_createdAt_idx" ON "AvatarCharacterHistory"("avatarCharacterJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "AvatarCharacterRegistry" (
  "id" TEXT PRIMARY KEY,
  "slot" TEXT NOT NULL UNIQUE,
  "characterId" TEXT,
  "uniqueId" TEXT,
  "name" TEXT,
  "snapshot" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AvatarCharacterRegistry_characterId_idx" ON "AvatarCharacterRegistry"("characterId");
CREATE INDEX IF NOT EXISTS "AvatarCharacterRegistry_active_idx" ON "AvatarCharacterRegistry"("active");
