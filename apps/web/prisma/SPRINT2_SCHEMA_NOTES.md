-- Sprint 2/3 schema alignment for RTAS Studio AI (PostgreSQL / Supabase)
-- Idempotent where possible. Apply via: npm run db:push -w @rtas/web
-- or: npx prisma db push --schema=prisma/schema.prisma

-- Prefer Prisma db push from apps/web (source of truth is schema.prisma).
-- This file documents the expected production shape for operators.

-- Project table
-- GenerationJob: projectId, audioUrl, creditsDebited, provider, settings,
--   progressPercent, stageLabel, queuePosition, estimatedSecondsRemaining,
--   retryCount, startedAt, cancelledAt
-- GenerationJobStatus enum: QUEUED, PREPARING, GENERATING, GENERATING_CHUNKS,
--   RENDERING, COMPILING_MEDIA, UPLOADING, COMPLETED, FAILED, CANCELLED
