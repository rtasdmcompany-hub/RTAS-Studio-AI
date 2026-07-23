-- Phase 13 Sprint 9 — Feedback portal votes + status tracking
-- Extends CustomerFeedback; adds FeedbackVotes. No seed data / fake votes.

ALTER TABLE "CustomerFeedback" ADD COLUMN IF NOT EXISTS "title" TEXT NOT NULL DEFAULT '';
ALTER TABLE "CustomerFeedback" ADD COLUMN IF NOT EXISTS "status" TEXT NOT NULL DEFAULT 'received';
ALTER TABLE "CustomerFeedback" ADD COLUMN IF NOT EXISTS "voteCount" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CustomerFeedback" ADD COLUMN IF NOT EXISTS "isPublic" BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE "CustomerFeedback" ADD COLUMN IF NOT EXISTS "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS "CustomerFeedback_status_voteCount_idx" ON "CustomerFeedback"("status", "voteCount" DESC);
CREATE INDEX IF NOT EXISTS "CustomerFeedback_isPublic_status_voteCount_idx" ON "CustomerFeedback"("isPublic", "status", "voteCount" DESC);

CREATE TABLE IF NOT EXISTS "FeedbackVotes" (
  "id" TEXT NOT NULL,
  "feedbackId" TEXT NOT NULL,
  "voterKey" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "FeedbackVotes_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "FeedbackVotes_feedbackId_voterKey_key" ON "FeedbackVotes"("feedbackId", "voterKey");
CREATE INDEX IF NOT EXISTS "FeedbackVotes_feedbackId_createdAt_idx" ON "FeedbackVotes"("feedbackId", "createdAt" DESC);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'FeedbackVotes_feedbackId_fkey'
  ) THEN
    ALTER TABLE "FeedbackVotes"
      ADD CONSTRAINT "FeedbackVotes_feedbackId_fkey"
      FOREIGN KEY ("feedbackId") REFERENCES "CustomerFeedback"("id")
      ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;
