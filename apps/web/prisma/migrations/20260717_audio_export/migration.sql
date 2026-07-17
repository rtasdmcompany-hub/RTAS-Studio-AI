-- Phase 4 Sprint 9 — Audio Export, Delivery & Distribution (UP)
-- Reversible: see migration_down.sql in this folder.

CREATE TABLE IF NOT EXISTS "ExportJob" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "backendJobId" TEXT UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'queued',
  "platform" TEXT NOT NULL DEFAULT 'youtube',
  "profileId" TEXT,
  "quality" TEXT NOT NULL DEFAULT 'high',
  "videoFormat" TEXT,
  "audioFormat" TEXT,
  "resolution" TEXT,
  "watermark" BOOLEAN NOT NULL DEFAULT false,
  "batchId" TEXT,
  "packageUrl" TEXT,
  "downloadUrl" TEXT,
  "signedUrl" TEXT,
  "expiresAt" TIMESTAMP(3),
  "productionReady" BOOLEAN NOT NULL DEFAULT false,
  "verified" BOOLEAN NOT NULL DEFAULT false,
  "exportSizeBytes" INTEGER NOT NULL DEFAULT 0,
  "downloadCount" INTEGER NOT NULL DEFAULT 0,
  "exportVersion" INTEGER NOT NULL DEFAULT 1,
  "retryCount" INTEGER NOT NULL DEFAULT 0,
  "queuePosition" INTEGER,
  "errorMessage" TEXT,
  "resumeToken" TEXT,
  "provider" TEXT,
  "parentTimelineJobId" TEXT,
  "parentVideoJobId" TEXT,
  "parentLocalizationJobId" TEXT,
  "parentMixJobId" TEXT,
  "parentGenerationId" TEXT,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completedAt" TIMESTAMP(3)
);
CREATE INDEX IF NOT EXISTS "ExportJob_userId_createdAt_idx" ON "ExportJob"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ExportJob_status_idx" ON "ExportJob"("status");
CREATE INDEX IF NOT EXISTS "ExportJob_platform_idx" ON "ExportJob"("platform");
CREATE INDEX IF NOT EXISTS "ExportJob_backendJobId_idx" ON "ExportJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "ExportJob_batchId_idx" ON "ExportJob"("batchId");
CREATE INDEX IF NOT EXISTS "ExportJob_parentGenerationId_idx" ON "ExportJob"("parentGenerationId");

CREATE TABLE IF NOT EXISTS "ExportProfileRecord" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "profileId" TEXT NOT NULL,
  "platform" TEXT NOT NULL,
  "label" TEXT,
  "videoFormat" TEXT,
  "audioFormat" TEXT,
  "resolution" TEXT,
  "width" INTEGER,
  "height" INTEGER,
  "videoBitrateKbps" INTEGER,
  "audioBitrateKbps" INTEGER,
  "audioLoudnessLufs" DOUBLE PRECISION,
  "videoCodec" TEXT,
  "audioCodec" TEXT,
  "fps" DOUBLE PRECISION,
  "aspectRatio" TEXT,
  "metadataFormat" TEXT,
  "settings" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ExportProfileRecord_exportJobId_idx" ON "ExportProfileRecord"("exportJobId");
CREATE INDEX IF NOT EXISTS "ExportProfileRecord_profileId_idx" ON "ExportProfileRecord"("profileId");
CREATE INDEX IF NOT EXISTS "ExportProfileRecord_platform_idx" ON "ExportProfileRecord"("platform");

CREATE TABLE IF NOT EXISTS "ExportAssetRecord" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "assetId" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "format" TEXT NOT NULL,
  "url" TEXT,
  "sizeBytes" INTEGER NOT NULL DEFAULT 0,
  "checksum" TEXT,
  "mimeType" TEXT,
  "verified" BOOLEAN NOT NULL DEFAULT false,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ExportAssetRecord_exportJobId_idx" ON "ExportAssetRecord"("exportJobId");
CREATE INDEX IF NOT EXISTS "ExportAssetRecord_assetId_idx" ON "ExportAssetRecord"("assetId");
CREATE INDEX IF NOT EXISTS "ExportAssetRecord_kind_idx" ON "ExportAssetRecord"("kind");

CREATE TABLE IF NOT EXISTS "ExportHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "status" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ExportHistoryEntry_exportJobId_createdAt_idx" ON "ExportHistoryEntry"("exportJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "DeliveryLog" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "event" TEXT NOT NULL,
  "url" TEXT,
  "signed" BOOLEAN NOT NULL DEFAULT false,
  "details" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "DeliveryLog_exportJobId_createdAt_idx" ON "DeliveryLog"("exportJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "DownloadHistoryEntry" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "authorized" BOOLEAN NOT NULL DEFAULT false,
  "downloadCount" INTEGER NOT NULL DEFAULT 0,
  "details" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "DownloadHistoryEntry_exportJobId_createdAt_idx" ON "DownloadHistoryEntry"("exportJobId", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "ExportAnalyticsRecord" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "platform" TEXT,
  "format" TEXT,
  "sizeBytes" INTEGER NOT NULL DEFAULT 0,
  "processingTimeMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "downloadCount" INTEGER NOT NULL DEFAULT 0,
  "success" BOOLEAN NOT NULL DEFAULT false,
  "compressionRatio" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ExportAnalyticsRecord_exportJobId_idx" ON "ExportAnalyticsRecord"("exportJobId");
CREATE INDEX IF NOT EXISTS "ExportAnalyticsRecord_platform_idx" ON "ExportAnalyticsRecord"("platform");

CREATE TABLE IF NOT EXISTS "ExportVersionRecord" (
  "id" TEXT PRIMARY KEY,
  "exportJobId" TEXT,
  "version" INTEGER NOT NULL,
  "label" TEXT,
  "snapshot" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ExportVersionRecord_exportJobId_version_idx" ON "ExportVersionRecord"("exportJobId", "version");
