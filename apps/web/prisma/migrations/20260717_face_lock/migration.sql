-- Phase 5 Sprint 2 — AI Face Lock & Identity Engine (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "FaceLockJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "characterId" TEXT NOT NULL,
  "lockId" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'locked',
  "faceEmbeddingRef" TEXT,
  "identityStrength" DOUBLE PRECISION NOT NULL DEFAULT 0.95,
  "identityScore" DOUBLE PRECISION,
  "driftDetected" BOOLEAN NOT NULL DEFAULT false,
  "featuresJson" JSONB,
  "referenceUrl" TEXT,
  "referenceKind" TEXT,
  "version" INTEGER NOT NULL DEFAULT 1,
  "productionReady" BOOLEAN NOT NULL DEFAULT true,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "FaceLockJob_characterId_idx" ON "FaceLockJob"("characterId");
CREATE INDEX IF NOT EXISTS "FaceLockJob_lockId_idx" ON "FaceLockJob"("lockId");
CREATE INDEX IF NOT EXISTS "FaceLockJob_faceEmbeddingRef_idx" ON "FaceLockJob"("faceEmbeddingRef");
CREATE INDEX IF NOT EXISTS "FaceLockJob_status_idx" ON "FaceLockJob"("status");

CREATE TABLE IF NOT EXISTS "FaceEmbeddingRecord" (
  "id" TEXT PRIMARY KEY,
  "faceLockJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "faceEmbeddingRef" TEXT NOT NULL,
  "dimension" INTEGER NOT NULL DEFAULT 64,
  "locked" BOOLEAN NOT NULL DEFAULT true,
  "regenerated" BOOLEAN NOT NULL DEFAULT false,
  "vector" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "FaceEmbeddingRecord_characterId_idx" ON "FaceEmbeddingRecord"("characterId");
CREATE INDEX IF NOT EXISTS "FaceEmbeddingRecord_faceEmbeddingRef_idx" ON "FaceEmbeddingRecord"("faceEmbeddingRef");
CREATE INDEX IF NOT EXISTS "FaceEmbeddingRecord_faceLockJobId_idx" ON "FaceEmbeddingRecord"("faceLockJobId");

CREATE TABLE IF NOT EXISTS "IdentityVerificationRecord" (
  "id" TEXT PRIMARY KEY,
  "faceLockJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "identityScore" DOUBLE PRECISION NOT NULL,
  "passed" BOOLEAN NOT NULL DEFAULT false,
  "driftDetected" BOOLEAN NOT NULL DEFAULT false,
  "cosineSimilarity" DOUBLE PRECISION,
  "driftFlags" JSONB,
  "notes" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "IdentityVerificationRecord_characterId_createdAt_idx" ON "IdentityVerificationRecord"("characterId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "IdentityVerificationRecord_faceLockJobId_idx" ON "IdentityVerificationRecord"("faceLockJobId");

CREATE TABLE IF NOT EXISTS "FaceReferenceRecord" (
  "id" TEXT PRIMARY KEY,
  "faceLockJobId" TEXT,
  "characterId" TEXT NOT NULL,
  "referenceId" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "url" TEXT NOT NULL,
  "source" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "FaceReferenceRecord_characterId_idx" ON "FaceReferenceRecord"("characterId");
CREATE INDEX IF NOT EXISTS "FaceReferenceRecord_kind_idx" ON "FaceReferenceRecord"("kind");
CREATE INDEX IF NOT EXISTS "FaceReferenceRecord_faceLockJobId_idx" ON "FaceReferenceRecord"("faceLockJobId");
