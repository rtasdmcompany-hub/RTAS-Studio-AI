-- Phase 8 Sprint 5 — Invoicing, Tax, Coupons & Billing Automation (UP)

ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "discountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "taxType" TEXT NOT NULL DEFAULT 'none';
ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "taxRate" DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "country" TEXT NOT NULL DEFAULT 'US';
ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "couponCode" TEXT;
ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "receiptNumber" TEXT;
ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS "pdfMetadataJson" JSONB;

CREATE TABLE IF NOT EXISTS "InvoiceItems" (
  "id" TEXT PRIMARY KEY,
  "invoiceId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "quantity" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "unitPriceUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "InvoiceItems_invoiceId_idx" ON "InvoiceItems"("invoiceId");
CREATE INDEX IF NOT EXISTS "InvoiceItems_organizationId_idx" ON "InvoiceItems"("organizationId");

CREATE TABLE IF NOT EXISTS "TaxRecords" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "invoiceId" TEXT,
  "country" TEXT NOT NULL,
  "taxType" TEXT NOT NULL,
  "rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "taxableUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "taxUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "exempt" BOOLEAN NOT NULL DEFAULT false,
  "exemptionReason" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "TaxRecords_organizationId_createdAt_idx"
  ON "TaxRecords"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "TaxRecords_invoiceId_idx" ON "TaxRecords"("invoiceId");
CREATE INDEX IF NOT EXISTS "TaxRecords_country_taxType_idx" ON "TaxRecords"("country", "taxType");

CREATE TABLE IF NOT EXISTS "Coupons" (
  "id" TEXT PRIMARY KEY,
  "code" TEXT NOT NULL UNIQUE,
  "couponType" TEXT NOT NULL,
  "percentOff" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "amountOffUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "category" TEXT NOT NULL DEFAULT 'promotional',
  "maxRedemptions" INTEGER NOT NULL DEFAULT 100,
  "redemptionCount" INTEGER NOT NULL DEFAULT 0,
  "perOrgLimit" INTEGER NOT NULL DEFAULT 1,
  "trialDays" INTEGER NOT NULL DEFAULT 0,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "expiresAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Coupons_couponType_idx" ON "Coupons"("couponType");
CREATE INDEX IF NOT EXISTS "Coupons_active_expiresAt_idx" ON "Coupons"("active", "expiresAt");

CREATE TABLE IF NOT EXISTS "CouponUsage" (
  "id" TEXT PRIMARY KEY,
  "couponId" TEXT NOT NULL,
  "couponCode" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "actorId" TEXT,
  "discountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "invoiceId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CouponUsage_organizationId_createdAt_idx"
  ON "CouponUsage"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CouponUsage_couponId_idx" ON "CouponUsage"("couponId");
CREATE INDEX IF NOT EXISTS "CouponUsage_couponCode_idx" ON "CouponUsage"("couponCode");

CREATE TABLE IF NOT EXISTS "Discounts" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "discountType" TEXT NOT NULL,
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "percentOff" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "couponCode" TEXT,
  "invoiceId" TEXT,
  "reason" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Discounts_organizationId_createdAt_idx"
  ON "Discounts"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Discounts_couponCode_idx" ON "Discounts"("couponCode");

CREATE TABLE IF NOT EXISTS "PaymentRetries" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "invoiceId" TEXT NOT NULL,
  "attempt" INTEGER NOT NULL DEFAULT 0,
  "maxAttempts" INTEGER NOT NULL DEFAULT 3,
  "status" TEXT NOT NULL DEFAULT 'scheduled',
  "nextRetryAt" TIMESTAMP(3),
  "lastError" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PaymentRetries_organizationId_createdAt_idx"
  ON "PaymentRetries"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PaymentRetries_invoiceId_idx" ON "PaymentRetries"("invoiceId");
CREATE INDEX IF NOT EXISTS "PaymentRetries_status_nextRetryAt_idx"
  ON "PaymentRetries"("status", "nextRetryAt");
