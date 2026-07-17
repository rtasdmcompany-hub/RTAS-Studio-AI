-- Phase 5 Sprint 8 — AI Cinematic Environment & World Generation Engine (UP)

CREATE TABLE IF NOT EXISTS "EnvironmentJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "worldId" TEXT,
  "sceneId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "environmentId" TEXT,
  "weatherType" TEXT,
  "lightingProfile" TEXT,
  "timeOfDay" TEXT,
  "consistencyScore" DOUBLE PRECISION,
  "consistent" BOOLEAN NOT NULL DEFAULT false,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "version" INTEGER NOT NULL DEFAULT 1,
  "analysisJson" JSONB,
  "environmentJson" JSONB,
  "consistencyJson" JSONB,
  "integrationsJson" JSONB,
  "metadata" JSONB,
  "error" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EnvironmentJob_worldId_idx" ON "EnvironmentJob"("worldId");
CREATE INDEX IF NOT EXISTS "EnvironmentJob_sceneId_idx" ON "EnvironmentJob"("sceneId");
CREATE INDEX IF NOT EXISTS "EnvironmentJob_backendJobId_idx" ON "EnvironmentJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "EnvironmentJob_status_idx" ON "EnvironmentJob"("status");
CREATE INDEX IF NOT EXISTS "EnvironmentJob_environmentId_idx" ON "EnvironmentJob"("environmentId");
CREATE INDEX IF NOT EXISTS "EnvironmentJob_weatherType_idx" ON "EnvironmentJob"("weatherType");
CREATE INDEX IF NOT EXISTS "EnvironmentJob_createdAt_idx" ON "EnvironmentJob"("createdAt" DESC);

CREATE TABLE IF NOT EXISTS "WorldLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "worldId" TEXT NOT NULL UNIQUE,
  "name" TEXT,
  "environmentId" TEXT,
  "locationId" TEXT,
  "fingerprint" TEXT,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "WorldLibraryEntry_environmentId_idx" ON "WorldLibraryEntry"("environmentId");
CREATE INDEX IF NOT EXISTS "WorldLibraryEntry_locationId_idx" ON "WorldLibraryEntry"("locationId");
CREATE INDEX IF NOT EXISTS "WorldLibraryEntry_fingerprint_idx" ON "WorldLibraryEntry"("fingerprint");

CREATE TABLE IF NOT EXISTS "LocationLibraryEntry" (
  "id" TEXT PRIMARY KEY,
  "locationId" TEXT NOT NULL UNIQUE,
  "worldId" TEXT,
  "environmentId" TEXT,
  "name" TEXT,
  "assetsJson" JSONB,
  "sky" TEXT,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LocationLibraryEntry_worldId_idx" ON "LocationLibraryEntry"("worldId");
CREATE INDEX IF NOT EXISTS "LocationLibraryEntry_environmentId_idx" ON "LocationLibraryEntry"("environmentId");

CREATE TABLE IF NOT EXISTS "WeatherProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "weatherId" TEXT NOT NULL UNIQUE,
  "moodSync" TEXT,
  "intensity" DOUBLE PRECISION,
  "precipitation" DOUBLE PRECISION,
  "visibility" DOUBLE PRECISION,
  "wind" DOUBLE PRECISION,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "WeatherProfileRecord_weatherId_idx" ON "WeatherProfileRecord"("weatherId");
CREATE INDEX IF NOT EXISTS "WeatherProfileRecord_moodSync_idx" ON "WeatherProfileRecord"("moodSync");

CREATE TABLE IF NOT EXISTS "LightingProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "lightingId" TEXT NOT NULL UNIQUE,
  "style" TEXT,
  "softHard" TEXT,
  "rim" BOOLEAN NOT NULL DEFAULT false,
  "hdr" BOOLEAN NOT NULL DEFAULT true,
  "shadows" TEXT,
  "reflections" DOUBLE PRECISION,
  "giStrength" DOUBLE PRECISION,
  "colorTempK" INTEGER,
  "payloadJson" JSONB,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "LightingProfileRecord_lightingId_idx" ON "LightingProfileRecord"("lightingId");
CREATE INDEX IF NOT EXISTS "LightingProfileRecord_style_idx" ON "LightingProfileRecord"("style");

CREATE TABLE IF NOT EXISTS "EnvironmentMetadataRecord" (
  "id" TEXT PRIMARY KEY,
  "environmentJobId" TEXT,
  "worldId" TEXT,
  "sceneId" TEXT,
  "weatherType" TEXT,
  "lightingProfile" TEXT,
  "processingTimeMs" DOUBLE PRECISION,
  "queueTimeMs" DOUBLE PRECISION,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "errorsJson" JSONB,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "EnvironmentMetadataRecord_environmentJobId_idx" ON "EnvironmentMetadataRecord"("environmentJobId");
CREATE INDEX IF NOT EXISTS "EnvironmentMetadataRecord_worldId_idx" ON "EnvironmentMetadataRecord"("worldId");
CREATE INDEX IF NOT EXISTS "EnvironmentMetadataRecord_sceneId_idx" ON "EnvironmentMetadataRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "EnvironmentMetadataRecord_weatherType_idx" ON "EnvironmentMetadataRecord"("weatherType");

CREATE TABLE IF NOT EXISTS "WorldHistoryRecord" (
  "id" TEXT PRIMARY KEY,
  "environmentJobId" TEXT,
  "worldId" TEXT NOT NULL,
  "sceneId" TEXT,
  "environmentId" TEXT,
  "weatherType" TEXT,
  "lightingProfile" TEXT,
  "consistencyScore" DOUBLE PRECISION,
  "fingerprint" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "WorldHistoryRecord_worldId_createdAt_idx" ON "WorldHistoryRecord"("worldId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "WorldHistoryRecord_sceneId_idx" ON "WorldHistoryRecord"("sceneId");
CREATE INDEX IF NOT EXISTS "WorldHistoryRecord_environmentJobId_idx" ON "WorldHistoryRecord"("environmentJobId");
CREATE INDEX IF NOT EXISTS "WorldHistoryRecord_fingerprint_idx" ON "WorldHistoryRecord"("fingerprint");

DO $$ BEGIN
  ALTER TABLE "WorldHistoryRecord"
    ADD CONSTRAINT "WorldHistoryRecord_environmentJobId_fkey"
    FOREIGN KEY ("environmentJobId") REFERENCES "EnvironmentJob"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
