-- Phase 8 Sprint 3 — PayPal Payments & Credit Wallet (UP)

-- Extend CreditWallets
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "bonusBalance" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "trialBalance" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "promoBalance" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "lifetimePurchased" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "lifetimeConsumed" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "lifetimeRefunded" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "lifetimeAwarded" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "CreditWallets" ADD COLUMN IF NOT EXISTS "expiresAt" TIMESTAMP(3);

-- Extend CreditTransactions
ALTER TABLE "CreditTransactions" ADD COLUMN IF NOT EXISTS "creditCategory" TEXT NOT NULL DEFAULT 'purchased';
ALTER TABLE "CreditTransactions" ADD COLUMN IF NOT EXISTS "expiresAt" TIMESTAMP(3);
CREATE INDEX IF NOT EXISTS "CreditTransactions_txnType_idx" ON "CreditTransactions"("txnType");

CREATE TABLE IF NOT EXISTS "PayPalPayments" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "paypalOrderId" TEXT NOT NULL UNIQUE,
  "paypalCaptureId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'CREATED',
  "intent" TEXT NOT NULL DEFAULT 'CAPTURE',
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "packKey" TEXT,
  "credits" INTEGER NOT NULL DEFAULT 0,
  "bonusCredits" INTEGER NOT NULL DEFAULT 0,
  "payerEmail" TEXT,
  "actorId" TEXT,
  "verified" BOOLEAN NOT NULL DEFAULT false,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PayPalPayments_organizationId_createdAt_idx"
  ON "PayPalPayments"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PayPalPayments_status_idx" ON "PayPalPayments"("status");
CREATE INDEX IF NOT EXISTS "PayPalPayments_paypalCaptureId_idx" ON "PayPalPayments"("paypalCaptureId");

CREATE TABLE IF NOT EXISTS "PaymentHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "paymentId" TEXT NOT NULL,
  "provider" TEXT NOT NULL DEFAULT 'paypal',
  "action" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT '',
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "detail" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PaymentHistory_organizationId_createdAt_idx"
  ON "PaymentHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PaymentHistory_paymentId_createdAt_idx"
  ON "PaymentHistory"("paymentId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PaymentHistory_provider_action_idx"
  ON "PaymentHistory"("provider", "action");

CREATE TABLE IF NOT EXISTS "RefundRequests" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "paymentId" TEXT,
  "walletTxnId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "credits" INTEGER NOT NULL DEFAULT 0,
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "reason" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "reviewerId" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "RefundRequests_organizationId_createdAt_idx"
  ON "RefundRequests"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "RefundRequests_paymentId_idx" ON "RefundRequests"("paymentId");
CREATE INDEX IF NOT EXISTS "RefundRequests_status_idx" ON "RefundRequests"("status");

CREATE TABLE IF NOT EXISTS "RefundHistory" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "refundRequestId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "detail" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "RefundHistory_organizationId_createdAt_idx"
  ON "RefundHistory"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "RefundHistory_refundRequestId_createdAt_idx"
  ON "RefundHistory"("refundRequestId", "createdAt" DESC);
