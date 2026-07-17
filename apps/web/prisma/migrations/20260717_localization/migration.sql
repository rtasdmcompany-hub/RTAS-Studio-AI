-- Phase 4 Sprint 7 — Multi-Language Dubbing & Localization (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "LocalizationJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "kind" TEXT NOT NULL DEFAULT 'localize',
  "sourceLanguage" TEXT NOT NULL DEFAULT 'en',
  "targetLanguage" TEXT NOT NULL,
  "sourceText" TEXT NOT NULL,
  "translatedText" TEXT,
  "accentProfile" TEXT,
  "voicePreserved" BOOLEAN NOT NULL DEFAULT true,
  "speakerCount" INTEGER NOT NULL DEFAULT 1,
  "subtitleUrl" TEXT,
  "captionUrl" TEXT,
  "dubbedAudioUrl" TEXT,
  "provider" TEXT,
  "localizationVersion" INTEGER NOT NULL DEFAULT 1,
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "parentVoiceJobId" TEXT,
  "parentCloneId" TEXT,
  "parentVideoJobId" TEXT,
  "parentGenerationId" TEXT,
  "lipSyncMetadata" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "LocalizationJob_userId_createdAt_idx" ON "LocalizationJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "LocalizationJob_status_idx" ON "LocalizationJob"("status");
CREATE INDEX IF NOT EXISTS "LocalizationJob_sourceLanguage_targetLanguage_idx" ON "LocalizationJob"("sourceLanguage", "targetLanguage");
CREATE INDEX IF NOT EXISTS "LocalizationJob_backendJobId_idx" ON "LocalizationJob"("backendJobId");

CREATE TABLE IF NOT EXISTS "LanguageProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "code" TEXT NOT NULL,
  "name" TEXT,
  "rtl" BOOLEAN NOT NULL DEFAULT false,
  "defaultLocale" TEXT,
  "accentDefault" TEXT,
  "script" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LanguageProfileRecord_code_idx" ON "LanguageProfileRecord"("code");
CREATE INDEX IF NOT EXISTS "LanguageProfileRecord_localizationJobId_idx" ON "LanguageProfileRecord"("localizationJobId");

CREATE TABLE IF NOT EXISTS "SubtitleAsset" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "language" TEXT NOT NULL,
  "format" TEXT NOT NULL DEFAULT 'vtt',
  "assetUrl" TEXT,
  "cueCount" INTEGER NOT NULL DEFAULT 0,
  "cues" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SubtitleAsset_localizationJobId_idx" ON "SubtitleAsset"("localizationJobId");
CREATE INDEX IF NOT EXISTS "SubtitleAsset_language_idx" ON "SubtitleAsset"("language");

CREATE TABLE IF NOT EXISTS "CaptionAsset" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "language" TEXT NOT NULL,
  "format" TEXT NOT NULL DEFAULT 'vtt',
  "assetUrl" TEXT,
  "cueCount" INTEGER NOT NULL DEFAULT 0,
  "cues" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CaptionAsset_localizationJobId_idx" ON "CaptionAsset"("localizationJobId");
CREATE INDEX IF NOT EXISTS "CaptionAsset_language_idx" ON "CaptionAsset"("language");

CREATE TABLE IF NOT EXISTS "SpeakerMap" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "speakerId" TEXT NOT NULL,
  "characterId" TEXT,
  "sourceVoiceId" TEXT,
  "cloneId" TEXT,
  "gender" TEXT,
  "accent" TEXT,
  "preserved" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SpeakerMap_localizationJobId_idx" ON "SpeakerMap"("localizationJobId");
CREATE INDEX IF NOT EXISTS "SpeakerMap_speakerId_idx" ON "SpeakerMap"("speakerId");
CREATE INDEX IF NOT EXISTS "SpeakerMap_characterId_idx" ON "SpeakerMap"("characterId");

CREATE TABLE IF NOT EXISTS "TranslationMemoryEntry" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "sourceLanguage" TEXT NOT NULL,
  "targetLanguage" TEXT NOT NULL,
  "sourceTextHash" TEXT NOT NULL,
  "sourceText" TEXT NOT NULL,
  "translatedText" TEXT NOT NULL,
  "hitCount" INTEGER NOT NULL DEFAULT 1,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TranslationMemoryEntry_langs_hash_idx" ON "TranslationMemoryEntry"("sourceLanguage", "targetLanguage", "sourceTextHash");
CREATE INDEX IF NOT EXISTS "TranslationMemoryEntry_localizationJobId_idx" ON "TranslationMemoryEntry"("localizationJobId");

CREATE TABLE IF NOT EXISTS "LocalizationHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LocalizationHistoryEntry_job_created_idx" ON "LocalizationHistoryEntry"("localizationJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "LocalizationAudioTrack" (
  "id" TEXT PRIMARY KEY,
  "localizationJobId" TEXT,
  "trackId" TEXT NOT NULL,
  "language" TEXT NOT NULL,
  "kind" TEXT NOT NULL DEFAULT 'dialogue',
  "assetUrl" TEXT,
  "durationSec" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "speakerId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LocalizationAudioTrack_localizationJobId_idx" ON "LocalizationAudioTrack"("localizationJobId");
CREATE INDEX IF NOT EXISTS "LocalizationAudioTrack_language_idx" ON "LocalizationAudioTrack"("language");
CREATE INDEX IF NOT EXISTS "LocalizationAudioTrack_trackId_idx" ON "LocalizationAudioTrack"("trackId");

CREATE TABLE IF NOT EXISTS "LocalizationLanguageCatalog" (
  "id" TEXT PRIMARY KEY,
  "code" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "nativeName" TEXT,
  "rtl" BOOLEAN NOT NULL DEFAULT false,
  "defaultLocale" TEXT,
  "accentDefault" TEXT,
  "script" TEXT,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LocalizationLanguageCatalog_active_idx" ON "LocalizationLanguageCatalog"("active");
