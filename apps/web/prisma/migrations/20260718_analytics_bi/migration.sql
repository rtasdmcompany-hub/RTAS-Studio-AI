-- Phase 7 Sprint 8 — Enterprise Reporting, Analytics & Business Intelligence Engine (UP)

CREATE TABLE IF NOT EXISTS "AnalyticsRecord" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "category" TEXT NOT NULL,
  "metricKey" TEXT NOT NULL,
  "metricValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "dimensionsJson" JSONB,
  "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AnalyticsRecord_organizationId_category_recordedAt_idx"
  ON "AnalyticsRecord"("organizationId", "category", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "AnalyticsRecord_workspaceId_recordedAt_idx"
  ON "AnalyticsRecord"("workspaceId", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "AnalyticsRecord_metricKey_idx" ON "AnalyticsRecord"("metricKey");

CREATE TABLE IF NOT EXISTS "BusinessMetric" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "name" TEXT NOT NULL,
  "value" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "unit" TEXT,
  "period" TEXT NOT NULL DEFAULT 'daily',
  "metadataJson" JSONB,
  "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "BusinessMetric_organizationId_name_recordedAt_idx"
  ON "BusinessMetric"("organizationId", "name", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "BusinessMetric_period_idx" ON "BusinessMetric"("period");

CREATE TABLE IF NOT EXISTS "KpiRecord" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "kpiKey" TEXT NOT NULL,
  "label" TEXT NOT NULL,
  "value" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "target" DOUBLE PRECISION,
  "unit" TEXT,
  "trend" TEXT,
  "metadataJson" JSONB,
  "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "KpiRecord_organizationId_kpiKey_recordedAt_idx"
  ON "KpiRecord"("organizationId", "kpiKey", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "KpiRecord_workspaceId_idx" ON "KpiRecord"("workspaceId");

CREATE TABLE IF NOT EXISTS "AnalyticsReportHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "generatedById" TEXT,
  "reportType" TEXT NOT NULL,
  "scope" TEXT NOT NULL DEFAULT 'organization',
  "title" TEXT NOT NULL,
  "periodStart" TIMESTAMP(3),
  "periodEnd" TIMESTAMP(3),
  "status" TEXT NOT NULL DEFAULT 'ready',
  "payloadJson" JSONB,
  "durationMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AnalyticsReportHistory_organizationId_reportType_createdAt_idx"
  ON "AnalyticsReportHistory"("organizationId", "reportType", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AnalyticsReportHistory_scope_idx" ON "AnalyticsReportHistory"("scope");
CREATE INDEX IF NOT EXISTS "AnalyticsReportHistory_generatedById_idx" ON "AnalyticsReportHistory"("generatedById");

CREATE TABLE IF NOT EXISTS "UsageStatistic" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "usageType" TEXT NOT NULL,
  "count" INTEGER NOT NULL DEFAULT 0,
  "bytes" BIGINT NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "periodStart" TIMESTAMP(3),
  "periodEnd" TIMESTAMP(3),
  "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "UsageStatistic_organizationId_usageType_recordedAt_idx"
  ON "UsageStatistic"("organizationId", "usageType", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "UsageStatistic_workspaceId_idx" ON "UsageStatistic"("workspaceId");

CREATE TABLE IF NOT EXISTS "PerformanceStatistic" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "metricKey" TEXT NOT NULL,
  "avgMs" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "p95Ms" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "successRate" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "sampleCount" INTEGER NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PerformanceStatistic_organizationId_metricKey_recordedAt_idx"
  ON "PerformanceStatistic"("organizationId", "metricKey", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "PerformanceStatistic_workspaceId_idx" ON "PerformanceStatistic"("workspaceId");

CREATE TABLE IF NOT EXISTS "ForecastRecord" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "metricKey" TEXT NOT NULL,
  "horizonDays" INTEGER NOT NULL DEFAULT 30,
  "predictedValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "confidence" DOUBLE PRECISION NOT NULL DEFAULT 0.7,
  "method" TEXT NOT NULL DEFAULT 'linear',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ForecastRecord_organizationId_metricKey_createdAt_idx"
  ON "ForecastRecord"("organizationId", "metricKey", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "ForecastRecord_workspaceId_idx" ON "ForecastRecord"("workspaceId");
