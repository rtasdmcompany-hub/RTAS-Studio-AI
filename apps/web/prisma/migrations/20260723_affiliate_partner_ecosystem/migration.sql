-- Phase 13 Sprint 5 — Affiliate, partnership & channel sales ecosystem

CREATE TABLE IF NOT EXISTS "AffiliateApplications" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "name" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "company" TEXT NOT NULL DEFAULT '',
  "website" TEXT NOT NULL DEFAULT '',
  "audienceSize" TEXT NOT NULL DEFAULT '',
  "channels" TEXT NOT NULL DEFAULT '',
  "audienceDescription" TEXT NOT NULL DEFAULT '',
  "promotionPlan" TEXT NOT NULL,
  "payoutPreference" TEXT NOT NULL DEFAULT '',
  "taxCountry" TEXT NOT NULL DEFAULT '',
  "acceptTerms" BOOLEAN NOT NULL DEFAULT false,
  "acceptProgramRules" BOOLEAN NOT NULL DEFAULT false,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "notes" TEXT NOT NULL DEFAULT '',
  "ip" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AffiliateApplications_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "AffiliateApplications_email_createdAt_idx"
  ON "AffiliateApplications"("email", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AffiliateApplications_status_createdAt_idx"
  ON "AffiliateApplications"("status", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AffiliateApplications_userId_idx"
  ON "AffiliateApplications"("userId");

CREATE TABLE IF NOT EXISTS "AffiliateAccounts" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "referralCode" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "applicationId" TEXT,
  "clicks" INTEGER NOT NULL DEFAULT 0,
  "signups" INTEGER NOT NULL DEFAULT 0,
  "paidConversions" INTEGER NOT NULL DEFAULT 0,
  "commissionCents" INTEGER NOT NULL DEFAULT 0,
  "paymentStatus" TEXT NOT NULL DEFAULT 'not_connected',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AffiliateAccounts_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS "AffiliateAccounts_userId_key" ON "AffiliateAccounts"("userId");
CREATE UNIQUE INDEX IF NOT EXISTS "AffiliateAccounts_referralCode_key" ON "AffiliateAccounts"("referralCode");
CREATE INDEX IF NOT EXISTS "AffiliateAccounts_status_idx" ON "AffiliateAccounts"("status");

CREATE TABLE IF NOT EXISTS "PartnerApplications" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT,
  "name" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "organization" TEXT NOT NULL,
  "role" TEXT NOT NULL DEFAULT '',
  "website" TEXT NOT NULL DEFAULT '',
  "partnerType" TEXT NOT NULL,
  "message" TEXT NOT NULL,
  "acceptTerms" BOOLEAN NOT NULL DEFAULT false,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "notes" TEXT NOT NULL DEFAULT '',
  "ip" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PartnerApplications_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS "PartnerApplications_email_createdAt_idx"
  ON "PartnerApplications"("email", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PartnerApplications_partnerType_status_idx"
  ON "PartnerApplications"("partnerType", "status");
CREATE INDEX IF NOT EXISTS "PartnerApplications_userId_idx"
  ON "PartnerApplications"("userId");

CREATE TABLE IF NOT EXISTS "PartnerAccounts" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "organization" TEXT NOT NULL,
  "partnerType" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "applicationId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "PartnerAccounts_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS "PartnerAccounts_userId_key" ON "PartnerAccounts"("userId");
CREATE INDEX IF NOT EXISTS "PartnerAccounts_status_partnerType_idx"
  ON "PartnerAccounts"("status", "partnerType");
