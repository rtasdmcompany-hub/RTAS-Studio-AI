-- Phase 4 Sprint 4 — Music Generation & Composition Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "MusicJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "genre" TEXT NOT NULL DEFAULT 'cinematic',
  "role" TEXT NOT NULL DEFAULT 'background',
  "title" TEXT,
  "bpm" INTEGER NOT NULL DEFAULT 90,
  "key" TEXT,
  "mood" TEXT,
  "energy" DOUBLE PRECISION NOT NULL DEFAULT 0.6,
  "intensity" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "durationSec" DOUBLE PRECISION NOT NULL DEFAULT 30,
  "instruments" JSONB,
  "loop" BOOLEAN NOT NULL DEFAULT false,
  "fadeInSec" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "fadeOutSec" DOUBLE PRECISION NOT NULL DEFAULT 2,
  "stems" JSONB,
  "assetUrl" TEXT,
  "previewUrl" TEXT,
  "stemUrls" JSONB,
  "libraryId" TEXT,
  "provider" TEXT,
  "musicVersion" INTEGER NOT NULL DEFAULT 1,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "sceneEmotion" TEXT,
  "sceneDurationSec" DOUBLE PRECISION,
  "cameraMotion" TEXT,
  "storyBeat" TEXT,
  "parentAudioJobId" TEXT,
  "parentVideoJobId" TEXT,
  "parentGenerationId" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "MusicJob_userId_createdAt_idx" ON "MusicJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "MusicJob_status_idx" ON "MusicJob"("status");
CREATE INDEX IF NOT EXISTS "MusicJob_genre_idx" ON "MusicJob"("genre");
CREATE INDEX IF NOT EXISTS "MusicJob_backendJobId_idx" ON "MusicJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "MusicJob_libraryId_idx" ON "MusicJob"("libraryId");

CREATE TABLE IF NOT EXISTS "MusicCompositionAsset" (
  "id" TEXT PRIMARY KEY,
  "musicJobId" TEXT,
  "format" TEXT NOT NULL DEFAULT 'wav',
  "assetUrl" TEXT,
  "filename" TEXT,
  "stemName" TEXT,
  "bytes" INTEGER,
  "checksum" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MusicCompositionAsset_musicJobId_idx" ON "MusicCompositionAsset"("musicJobId");

CREATE TABLE IF NOT EXISTS "MusicLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "musicJobId" TEXT,
  "libraryId" TEXT NOT NULL UNIQUE,
  "title" TEXT,
  "genre" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "bpm" INTEGER,
  "key" TEXT,
  "mood" TEXT,
  "durationSec" DOUBLE PRECISION,
  "instruments" JSONB,
  "loop" BOOLEAN NOT NULL DEFAULT false,
  "assetUrl" TEXT,
  "previewUrl" TEXT,
  "musicVersion" INTEGER NOT NULL DEFAULT 1,
  "tags" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MusicLibraryEntry_genre_idx" ON "MusicLibraryEntry"("genre");
CREATE INDEX IF NOT EXISTS "MusicLibraryEntry_role_idx" ON "MusicLibraryEntry"("role");
CREATE INDEX IF NOT EXISTS "MusicLibraryEntry_musicJobId_idx" ON "MusicLibraryEntry"("musicJobId");

CREATE TABLE IF NOT EXISTS "MusicMeta" (
  "id" TEXT PRIMARY KEY,
  "musicJobId" TEXT,
  "key" TEXT NOT NULL,
  "value" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MusicMeta_musicJobId_key_idx" ON "MusicMeta"("musicJobId", "key");

CREATE TABLE IF NOT EXISTS "MusicCompositionVersion" (
  "id" TEXT PRIMARY KEY,
  "musicJobId" TEXT,
  "version" INTEGER NOT NULL,
  "genre" TEXT,
  "bpm" INTEGER,
  "assetUrl" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MusicCompositionVersion_musicJobId_version_idx" ON "MusicCompositionVersion"("musicJobId", "version");

CREATE TABLE IF NOT EXISTS "MusicHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "musicJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MusicHistoryEntry_musicJobId_createdAt_idx" ON "MusicHistoryEntry"("musicJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "GenreLibrary" (
  "id" TEXT PRIMARY KEY,
  "code" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "defaultBpm" INTEGER NOT NULL DEFAULT 90,
  "defaultMood" TEXT,
  "defaultEnergy" DOUBLE PRECISION NOT NULL DEFAULT 0.6,
  "defaultKey" TEXT,
  "tags" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "GenreLibrary_active_idx" ON "GenreLibrary"("active");

CREATE TABLE IF NOT EXISTS "InstrumentLibrary" (
  "id" TEXT PRIMARY KEY,
  "code" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "family" TEXT,
  "genres" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "InstrumentLibrary_family_idx" ON "InstrumentLibrary"("family");
CREATE INDEX IF NOT EXISTS "InstrumentLibrary_active_idx" ON "InstrumentLibrary"("active");
