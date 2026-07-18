-- Phase 8 Sprint 2 — Paddle Billing Integration (UP)

CREATE TABLE IF NOT EXISTS "PaddleCustomers" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL UNIQUE,
  "paddleCustomerId" TEXT NOT NULL UNIQUE,
  "email" TEXT NOT NULL DEFAULT '',
  "name" TEXT NOT NULL DEFAULT '',
  "countryCode" TEXT NOT NULL DEFAULT '',
  "taxIdentifier" TEXT,
  "addressLine1" TEXT,
  "addressLine2" TEXT,
  "city" TEXT,
  "region" TEXT,
  "postalCode" TEXT,
  "status" TEXT NOT NULL DEFAULT 'active',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PaddleCustomers_email_idx" ON "PaddleCustomers"("email");

CREATE TABLE IF NOT EXISTS "PaddleSubscriptions" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL UNIQUE,
  "paddleSubscriptionId" TEXT NOT NULL UNIQUE,
  "paddleCustomerId" TEXT NOT NULL,
  "planKey" TEXT NOT NULL,
  "billingCycle" TEXT NOT NULL DEFAULT 'monthly',
  "status" TEXT NOT NULL DEFAULT 'active',
  "priceId" TEXT,
  "productId" TEXT,
  "cancelAtPeriodEnd" BOOLEAN NOT NULL DEFAULT false,
  "currentPeriodStart" TIMESTAMP(3),
  "currentPeriodEnd" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PaddleSubscriptions_status_idx" ON "PaddleSubscriptions"("status");
CREATE INDEX IF NOT EXISTS "PaddleSubscriptions_planKey_idx" ON "PaddleSubscriptions"("planKey");

CREATE TABLE IF NOT EXISTS "PaddleTransactions" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "paddleTransactionId" TEXT NOT NULL UNIQUE,
  "paddleSubscriptionId" TEXT,
  "paddleCustomerId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'completed',
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "eventType" TEXT NOT NULL DEFAULT 'transaction.completed',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PaddleTransactions_organizationId_createdAt_idx"
  ON "PaddleTransactions"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PaddleTransactions_eventType_idx" ON "PaddleTransactions"("eventType");

CREATE TABLE IF NOT EXISTS "PaddleWebhookLogs" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT,
  "eventId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "signatureValid" BOOLEAN NOT NULL DEFAULT false,
  "processed" BOOLEAN NOT NULL DEFAULT false,
  "error" TEXT,
  "payloadJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PaddleWebhookLogs_eventId_idx" ON "PaddleWebhookLogs"("eventId");
CREATE INDEX IF NOT EXISTS "PaddleWebhookLogs_eventType_createdAt_idx"
  ON "PaddleWebhookLogs"("eventType", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PaddleWebhookLogs_organizationId_idx" ON "PaddleWebhookLogs"("organizationId");

CREATE TABLE IF NOT EXISTS "BillingEvents" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "eventType" TEXT NOT NULL,
  "source" TEXT NOT NULL DEFAULT 'paddle',
  "actorId" TEXT,
  "detail" TEXT NOT NULL DEFAULT '',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "BillingEvents_organizationId_createdAt_idx"
  ON "BillingEvents"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "BillingEvents_eventType_idx" ON "BillingEvents"("eventType");
