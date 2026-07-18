-- Phase 8 Sprint 6 — Referral, Affiliate & Commission Engine (UP)

CREATE TABLE IF NOT EXISTS "ReferralCodes" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "ownerUserId" TEXT NOT NULL,
  "code" TEXT NOT NULL UNIQUE,
  "link" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "uses" INTEGER NOT NULL DEFAULT 0,
  "maxUses" INTEGER NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "ReferralCodes_organizationId_idx" ON "ReferralCodes"("organizationId");
CREATE INDEX IF NOT EXISTS "ReferralCodes_ownerUserId_idx" ON "ReferralCodes"("ownerUserId");
CREATE INDEX IF NOT EXISTS "ReferralCodes_active_idx" ON "ReferralCodes"("active");

CREATE TABLE IF NOT EXISTS "Referrals" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "referralCodeId" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "referrerUserId" TEXT NOT NULL,
  "referredEmail" TEXT NOT NULL DEFAULT '',
  "referredUserId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'invited',
  "rewardCredits" INTEGER NOT NULL DEFAULT 0,
  "referredBonusCredits" INTEGER NOT NULL DEFAULT 0,
  "invitedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "signedUpAt" TIMESTAMP(3),
  "convertedAt" TIMESTAMP(3),
  "rewardedAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Referrals_organizationId_createdAt_idx"
  ON "Referrals"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Referrals_referrerUserId_idx" ON "Referrals"("referrerUserId");
CREATE INDEX IF NOT EXISTS "Referrals_referredUserId_idx" ON "Referrals"("referredUserId");
CREATE INDEX IF NOT EXISTS "Referrals_status_idx" ON "Referrals"("status");

CREATE TABLE IF NOT EXISTS "Affiliates" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "name" TEXT NOT NULL DEFAULT '',
  "email" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'active',
  "commissionType" TEXT NOT NULL DEFAULT 'percentage',
  "commissionRate" DOUBLE PRECISION NOT NULL DEFAULT 20,
  "recurringRatePct" DOUBLE PRECISION NOT NULL DEFAULT 10,
  "payoutMethod" TEXT NOT NULL DEFAULT 'paypal',
  "parentAffiliateId" TEXT,
  "pendingUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "approvedUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "paidUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "lifetimeUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "Affiliates_organizationId_userId_key" UNIQUE ("organizationId", "userId")
);
CREATE INDEX IF NOT EXISTS "Affiliates_status_idx" ON "Affiliates"("status");
CREATE INDEX IF NOT EXISTS "Affiliates_parentAffiliateId_idx" ON "Affiliates"("parentAffiliateId");

CREATE TABLE IF NOT EXISTS "AffiliateCampaigns" (
  "id" TEXT PRIMARY KEY,
  "affiliateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "slug" TEXT NOT NULL UNIQUE,
  "link" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "clicks" INTEGER NOT NULL DEFAULT 0,
  "conversions" INTEGER NOT NULL DEFAULT 0,
  "revenueUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AffiliateCampaigns_affiliateId_idx" ON "AffiliateCampaigns"("affiliateId");
CREATE INDEX IF NOT EXISTS "AffiliateCampaigns_organizationId_idx" ON "AffiliateCampaigns"("organizationId");
CREATE INDEX IF NOT EXISTS "AffiliateCampaigns_active_idx" ON "AffiliateCampaigns"("active");

CREATE TABLE IF NOT EXISTS "AffiliateClicks" (
  "id" TEXT PRIMARY KEY,
  "affiliateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "campaignId" TEXT,
  "source" TEXT NOT NULL DEFAULT '',
  "referrerUrl" TEXT NOT NULL DEFAULT '',
  "ipHash" TEXT NOT NULL DEFAULT '',
  "userAgent" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AffiliateClicks_affiliateId_createdAt_idx"
  ON "AffiliateClicks"("affiliateId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AffiliateClicks_organizationId_idx" ON "AffiliateClicks"("organizationId");
CREATE INDEX IF NOT EXISTS "AffiliateClicks_campaignId_idx" ON "AffiliateClicks"("campaignId");

CREATE TABLE IF NOT EXISTS "AffiliateConversions" (
  "id" TEXT PRIMARY KEY,
  "affiliateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "campaignId" TEXT,
  "orderRef" TEXT NOT NULL DEFAULT '',
  "kind" TEXT NOT NULL DEFAULT 'one_time',
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AffiliateConversions_affiliateId_createdAt_idx"
  ON "AffiliateConversions"("affiliateId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "AffiliateConversions_organizationId_idx" ON "AffiliateConversions"("organizationId");
CREATE INDEX IF NOT EXISTS "AffiliateConversions_campaignId_idx" ON "AffiliateConversions"("campaignId");

CREATE TABLE IF NOT EXISTS "Commissions" (
  "id" TEXT PRIMARY KEY,
  "affiliateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "conversionId" TEXT,
  "level" INTEGER NOT NULL DEFAULT 1,
  "commissionType" TEXT NOT NULL DEFAULT 'percentage',
  "kind" TEXT NOT NULL DEFAULT 'one_time',
  "baseAmountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "payoutId" TEXT,
  "approvedAt" TIMESTAMP(3),
  "paidAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Commissions_affiliateId_createdAt_idx"
  ON "Commissions"("affiliateId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Commissions_organizationId_createdAt_idx"
  ON "Commissions"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Commissions_status_idx" ON "Commissions"("status");
CREATE INDEX IF NOT EXISTS "Commissions_conversionId_idx" ON "Commissions"("conversionId");

CREATE TABLE IF NOT EXISTS "PayoutRequests" (
  "id" TEXT PRIMARY KEY,
  "affiliateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'requested',
  "method" TEXT NOT NULL DEFAULT 'paypal',
  "note" TEXT NOT NULL DEFAULT '',
  "commissionIdsJson" JSONB,
  "requestedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "processedAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PayoutRequests_affiliateId_createdAt_idx"
  ON "PayoutRequests"("affiliateId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PayoutRequests_organizationId_createdAt_idx"
  ON "PayoutRequests"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PayoutRequests_status_idx" ON "PayoutRequests"("status");

CREATE TABLE IF NOT EXISTS "PayoutHistory" (
  "id" TEXT PRIMARY KEY,
  "payoutId" TEXT NOT NULL,
  "affiliateId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "amountUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "detail" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "PayoutHistory_payoutId_idx" ON "PayoutHistory"("payoutId");
CREATE INDEX IF NOT EXISTS "PayoutHistory_affiliateId_createdAt_idx"
  ON "PayoutHistory"("affiliateId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "PayoutHistory_organizationId_idx" ON "PayoutHistory"("organizationId");
