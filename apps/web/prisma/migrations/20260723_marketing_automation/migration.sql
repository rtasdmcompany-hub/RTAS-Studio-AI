-- Phase 13 Sprint 4 — Marketing automation & customer engagement
-- Integrity: metrics columns default to 0; metricsConnected=false until ESP webhooks.

CREATE TABLE IF NOT EXISTS "MarketingNotificationPreferences" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL UNIQUE,
  "emailTransactional" BOOLEAN NOT NULL DEFAULT true,
  "emailMarketing" BOOLEAN NOT NULL DEFAULT false,
  "emailBilling" BOOLEAN NOT NULL DEFAULT true,
  "emailProduct" BOOLEAN NOT NULL DEFAULT true,
  "inAppAnnouncements" BOOLEAN NOT NULL DEFAULT true,
  "inAppSecurity" BOOLEAN NOT NULL DEFAULT true,
  "inAppBilling" BOOLEAN NOT NULL DEFAULT true,
  "inAppMaintenance" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "MarketingNotificationPreferences_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "NewsletterSubscribers" (
  "id" TEXT PRIMARY KEY,
  "email" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL DEFAULT '',
  "userId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'subscribed',
  "source" TEXT NOT NULL DEFAULT 'web',
  "unsubscribedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "NewsletterSubscribers_status_createdAt_idx"
  ON "NewsletterSubscribers"("status", "createdAt" DESC);

CREATE TABLE IF NOT EXISTS "MarketingCampaigns" (
  "id" TEXT PRIMARY KEY,
  "name" TEXT NOT NULL,
  "templateId" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'planned',
  "segmentId" TEXT,
  "scheduledAt" TIMESTAMP(3),
  "queuedCount" INTEGER NOT NULL DEFAULT 0,
  "subscriberCount" INTEGER NOT NULL DEFAULT 0,
  "sentCount" INTEGER NOT NULL DEFAULT 0,
  "opensCount" INTEGER NOT NULL DEFAULT 0,
  "clicksCount" INTEGER NOT NULL DEFAULT 0,
  "bouncesCount" INTEGER NOT NULL DEFAULT 0,
  "unsubCount" INTEGER NOT NULL DEFAULT 0,
  "metricsConnected" BOOLEAN NOT NULL DEFAULT false,
  "notes" TEXT NOT NULL DEFAULT '',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "MarketingCampaigns_status_updatedAt_idx"
  ON "MarketingCampaigns"("status", "updatedAt" DESC);
CREATE INDEX IF NOT EXISTS "MarketingCampaigns_templateId_idx"
  ON "MarketingCampaigns"("templateId");

CREATE TABLE IF NOT EXISTS "CommercialLeads" (
  "id" TEXT PRIMARY KEY,
  "kind" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "company" TEXT NOT NULL DEFAULT '',
  "role" TEXT NOT NULL DEFAULT '',
  "website" TEXT NOT NULL DEFAULT '',
  "partnerType" TEXT NOT NULL DEFAULT '',
  "requestType" TEXT NOT NULL DEFAULT '',
  "useCase" TEXT NOT NULL DEFAULT '',
  "message" TEXT NOT NULL DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'new',
  "ip" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CommercialLeads_kind_createdAt_idx"
  ON "CommercialLeads"("kind", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CommercialLeads_email_createdAt_idx"
  ON "CommercialLeads"("email", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CommercialLeads_status_idx"
  ON "CommercialLeads"("status");

CREATE TABLE IF NOT EXISTS "StudioReferralCodes" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL UNIQUE,
  "code" TEXT NOT NULL UNIQUE,
  "link" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "uses" INTEGER NOT NULL DEFAULT 0,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "StudioReferralCodes_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS "StudioReferralCodes_active_idx"
  ON "StudioReferralCodes"("active");

CREATE TABLE IF NOT EXISTS "StudioReferrals" (
  "id" TEXT PRIMARY KEY,
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
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "StudioReferrals_referralCodeId_fkey"
    FOREIGN KEY ("referralCodeId") REFERENCES "StudioReferralCodes"("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "StudioReferrals_referrerUserId_fkey"
    FOREIGN KEY ("referrerUserId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS "StudioReferrals_referrerUserId_invitedAt_idx"
  ON "StudioReferrals"("referrerUserId", "invitedAt" DESC);
CREATE INDEX IF NOT EXISTS "StudioReferrals_code_idx" ON "StudioReferrals"("code");
CREATE INDEX IF NOT EXISTS "StudioReferrals_status_idx" ON "StudioReferrals"("status");

CREATE TABLE IF NOT EXISTS "SystemAnnouncements" (
  "id" TEXT PRIMARY KEY,
  "kind" TEXT NOT NULL DEFAULT 'announcement',
  "title" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "href" TEXT NOT NULL DEFAULT '',
  "active" BOOLEAN NOT NULL DEFAULT true,
  "startsAt" TIMESTAMP(3),
  "endsAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SystemAnnouncements_active_createdAt_idx"
  ON "SystemAnnouncements"("active", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "SystemAnnouncements_kind_idx" ON "SystemAnnouncements"("kind");

CREATE TABLE IF NOT EXISTS "EmailSendLogs" (
  "id" TEXT PRIMARY KEY,
  "templateId" TEXT NOT NULL,
  "toEmail" TEXT NOT NULL,
  "userId" TEXT,
  "subject" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'sent',
  "provider" TEXT,
  "error" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EmailSendLogs_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS "EmailSendLogs_templateId_createdAt_idx"
  ON "EmailSendLogs"("templateId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EmailSendLogs_userId_createdAt_idx"
  ON "EmailSendLogs"("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "EmailSendLogs_status_idx" ON "EmailSendLogs"("status");
