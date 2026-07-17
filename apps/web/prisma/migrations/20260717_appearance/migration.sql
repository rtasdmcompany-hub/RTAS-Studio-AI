-- Phase 5 Sprint 3 — AI Character Style & Appearance Engine (UP)

CREATE TABLE IF NOT EXISTS "AppearanceProfileJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "characterId" TEXT NOT NULL,
  "profileId" TEXT NOT NULL,
  "stylePresetId" TEXT,
  "activeOutfitId" TEXT,
  "appearanceScore" DOUBLE PRECISION,
  "driftDetected" BOOLEAN NOT NULL DEFAULT false,
  "profileJson" JSONB,
  "facialFingerprint" TEXT,
  "appearanceFingerprint" TEXT,
  "version" INTEGER NOT NULL DEFAULT 1,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AppearanceProfileJob_characterId_idx" ON "AppearanceProfileJob"("characterId");
CREATE INDEX IF NOT EXISTS "AppearanceProfileJob_profileId_idx" ON "AppearanceProfileJob"("profileId");
CREATE INDEX IF NOT EXISTS "AppearanceProfileJob_stylePresetId_idx" ON "AppearanceProfileJob"("stylePresetId");
CREATE INDEX IF NOT EXISTS "AppearanceProfileJob_activeOutfitId_idx" ON "AppearanceProfileJob"("activeOutfitId");

CREATE TABLE IF NOT EXISTS "AppearanceOutfitRecord" (
  "id" TEXT PRIMARY KEY,
  "appearanceProfileJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "outfitId" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "clothingStyle" TEXT NOT NULL,
  "shoes" TEXT NOT NULL,
  "accessories" JSONB,
  "custom" BOOLEAN NOT NULL DEFAULT false,
  "active" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AppearanceOutfitRecord_characterId_idx" ON "AppearanceOutfitRecord"("characterId");
CREATE INDEX IF NOT EXISTS "AppearanceOutfitRecord_outfitId_idx" ON "AppearanceOutfitRecord"("outfitId");
CREATE INDEX IF NOT EXISTS "AppearanceOutfitRecord_category_idx" ON "AppearanceOutfitRecord"("category");
CREATE INDEX IF NOT EXISTS "AppearanceOutfitRecord_appearanceProfileJobId_idx" ON "AppearanceOutfitRecord"("appearanceProfileJobId");

CREATE TABLE IF NOT EXISTS "AppearanceConsistencyRecord" (
  "id" TEXT PRIMARY KEY,
  "appearanceProfileJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "appearanceScore" DOUBLE PRECISION NOT NULL,
  "consistent" BOOLEAN NOT NULL DEFAULT false,
  "driftDetected" BOOLEAN NOT NULL DEFAULT false,
  "facePreserved" BOOLEAN NOT NULL DEFAULT true,
  "bodyPreserved" BOOLEAN NOT NULL DEFAULT true,
  "hairPreserved" BOOLEAN NOT NULL DEFAULT true,
  "clothingMatch" BOOLEAN NOT NULL DEFAULT true,
  "accessoriesMatch" BOOLEAN NOT NULL DEFAULT true,
  "driftFlags" JSONB,
  "notes" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AppearanceConsistencyRecord_characterId_createdAt_idx" ON "AppearanceConsistencyRecord"("characterId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AppearanceConsistencyRecord_appearanceProfileJobId_idx" ON "AppearanceConsistencyRecord"("appearanceProfileJobId");
