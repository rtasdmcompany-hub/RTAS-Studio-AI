-- Phase 10 Sprint 2 — Production performance indexes (UP)

-- Hot-path lookups for generation webhook / status polling
CREATE INDEX IF NOT EXISTS "GenerationJob_backendJobId_idx"
  ON "GenerationJob"("backendJobId");
CREATE INDEX IF NOT EXISTS "GenerationJob_status_createdAt_idx"
  ON "GenerationJob"("status", "createdAt" DESC);

-- Export job admin / status listings
CREATE INDEX IF NOT EXISTS "ExportJob_status_createdAt_idx"
  ON "ExportJob"("status", "createdAt" DESC);
