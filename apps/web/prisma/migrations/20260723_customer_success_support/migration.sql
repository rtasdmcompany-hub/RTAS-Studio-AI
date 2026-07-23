-- Phase 13 Sprint 6 — Customer success, support tickets & retention

ALTER TABLE "User" ADD COLUMN IF NOT EXISTS "lastLoginAt" TIMESTAMP(3);

CREATE TABLE IF NOT EXISTS "SupportTickets" (
  "id" TEXT PRIMARY KEY,
  "ticketNumber" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "priority" TEXT NOT NULL DEFAULT 'medium',
  "subject" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'open',
  "adminNotes" TEXT NOT NULL DEFAULT '',
  "resolvedAt" TIMESTAMP(3),
  "closedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "SupportTickets_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS "SupportTickets_ticketNumber_key" ON "SupportTickets"("ticketNumber");
CREATE INDEX IF NOT EXISTS "SupportTickets_userId_createdAt_idx" ON "SupportTickets"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "SupportTickets_status_priority_createdAt_idx" ON "SupportTickets"("status", "priority", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "SupportTickets_category_createdAt_idx" ON "SupportTickets"("category", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "SupportTicketReplies" (
  "id" TEXT PRIMARY KEY,
  "ticketId" TEXT NOT NULL,
  "authorRole" TEXT NOT NULL,
  "authorUserId" TEXT,
  "body" TEXT NOT NULL,
  "isInternal" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "SupportTicketReplies_ticketId_fkey" FOREIGN KEY ("ticketId") REFERENCES "SupportTickets"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "SupportTicketReplies_ticketId_createdAt_idx" ON "SupportTicketReplies"("ticketId", "createdAt" ASC);

CREATE TABLE IF NOT EXISTS "SupportTicketAttachments" (
  "id" TEXT PRIMARY KEY,
  "ticketId" TEXT NOT NULL,
  "fileName" TEXT NOT NULL,
  "contentType" TEXT NOT NULL DEFAULT 'application/octet-stream',
  "sizeBytes" INTEGER NOT NULL DEFAULT 0,
  "storageKey" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "SupportTicketAttachments_ticketId_fkey" FOREIGN KEY ("ticketId") REFERENCES "SupportTickets"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "SupportTicketAttachments_ticketId_idx" ON "SupportTicketAttachments"("ticketId");

CREATE TABLE IF NOT EXISTS "CustomerFeedback" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "email" TEXT,
  "kind" TEXT NOT NULL,
  "message" TEXT NOT NULL,
  "csatScore" INTEGER,
  "ipHash" TEXT,
  "source" TEXT NOT NULL DEFAULT '/feedback',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CustomerFeedback_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "CustomerFeedback_kind_createdAt_idx" ON "CustomerFeedback"("kind", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CustomerFeedback_userId_createdAt_idx" ON "CustomerFeedback"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CustomerFeedback_csatScore_idx" ON "CustomerFeedback"("csatScore");

CREATE TABLE IF NOT EXISTS "CustomerSurveyResponses" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "email" TEXT,
  "surveyType" TEXT NOT NULL,
  "score" INTEGER,
  "comment" TEXT,
  "metadataJson" JSONB,
  "source" TEXT NOT NULL DEFAULT '/feedback',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "CustomerSurveyResponses_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "CustomerSurveyResponses_surveyType_createdAt_idx" ON "CustomerSurveyResponses"("surveyType", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CustomerSurveyResponses_userId_createdAt_idx" ON "CustomerSurveyResponses"("userId", "createdAt" DESC);
