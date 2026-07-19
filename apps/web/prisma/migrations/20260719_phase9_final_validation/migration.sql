-- Phase 9 Sprint 10 — Final Integration & Marketplace Ecosystem Validation (UP)

CREATE TABLE IF NOT EXISTS "Phase9ValidationRuns" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT,
  "kind" TEXT NOT NULL,
  "passed" BOOLEAN NOT NULL DEFAULT FALSE,
  "score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "detailsJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Phase9ValidationRuns_organizationId_fkey" FOREIGN KEY ("organizationId")
    REFERENCES "Organization"("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "Phase9ValidationRuns_kind_createdAt_idx"
  ON "Phase9ValidationRuns"("kind", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Phase9ValidationRuns_organizationId_idx"
  ON "Phase9ValidationRuns"("organizationId");
CREATE INDEX IF NOT EXISTS "Phase9ValidationRuns_passed_idx"
  ON "Phase9ValidationRuns"("passed");
