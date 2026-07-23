-- Phase 13 Sprint 3 — Marketing lead capture (newsletter / updates / tips)
CREATE TABLE IF NOT EXISTS "MarketingLeads" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "kind" TEXT NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'web',
    "consentPrivacy" BOOLEAN NOT NULL DEFAULT false,
    "ipHash" TEXT,
    "userAgent" TEXT,
    "metadataJson" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "MarketingLeads_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "MarketingLeads_email_kind_key"
  ON "MarketingLeads"("email", "kind");

CREATE INDEX IF NOT EXISTS "MarketingLeads_kind_createdAt_idx"
  ON "MarketingLeads"("kind", "createdAt" DESC);

CREATE INDEX IF NOT EXISTS "MarketingLeads_createdAt_idx"
  ON "MarketingLeads"("createdAt" DESC);
