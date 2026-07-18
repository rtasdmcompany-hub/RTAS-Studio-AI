-- Phase 8 Sprint 1 — Enterprise Billing & Subscription Foundation (UP)

CREATE TABLE IF NOT EXISTS "SubscriptionPlans" (
  "id" TEXT PRIMARY KEY,
  "key" TEXT NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "monthlyPriceUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "yearlyPriceUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "creditsMonthly" INTEGER NOT NULL DEFAULT 0,
  "creditsYearly" INTEGER NOT NULL DEFAULT 0,
  "maxWorkspaces" INTEGER NOT NULL DEFAULT 1,
  "maxTeams" INTEGER NOT NULL DEFAULT 1,
  "maxMembers" INTEGER NOT NULL DEFAULT 3,
  "maxProjects" INTEGER NOT NULL DEFAULT 10,
  "aiProviderLimit" INTEGER NOT NULL DEFAULT 1,
  "featuresJson" JSONB,
  "isPublic" BOOLEAN NOT NULL DEFAULT true,
  "trialDays" INTEGER NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'active',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "SubscriptionPlans_status_isPublic_idx"
  ON "SubscriptionPlans"("status", "isPublic");

CREATE TABLE IF NOT EXISTS "UserSubscriptions" (
  "id" TEXT PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "planKey" TEXT NOT NULL,
  "billingCycle" TEXT NOT NULL DEFAULT 'monthly',
  "status" TEXT NOT NULL DEFAULT 'active',
  "organizationId" TEXT,
  "currentPeriodStart" TIMESTAMP(3),
  "currentPeriodEnd" TIMESTAMP(3),
  "cancelAtPeriodEnd" BOOLEAN NOT NULL DEFAULT false,
  "externalSubscriptionId" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "UserSubscriptions_userId_status_idx"
  ON "UserSubscriptions"("userId", "status");
CREATE INDEX IF NOT EXISTS "UserSubscriptions_organizationId_idx"
  ON "UserSubscriptions"("organizationId");
CREATE INDEX IF NOT EXISTS "UserSubscriptions_planKey_idx"
  ON "UserSubscriptions"("planKey");

CREATE TABLE IF NOT EXISTS "OrganizationSubscriptions" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL UNIQUE,
  "planKey" TEXT NOT NULL,
  "billingCycle" TEXT NOT NULL DEFAULT 'monthly',
  "status" TEXT NOT NULL DEFAULT 'active',
  "ownerUserId" TEXT,
  "seats" INTEGER NOT NULL DEFAULT 1,
  "currentPeriodStart" TIMESTAMP(3),
  "currentPeriodEnd" TIMESTAMP(3),
  "cancelAtPeriodEnd" BOOLEAN NOT NULL DEFAULT false,
  "externalSubscriptionId" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "OrganizationSubscriptions_planKey_status_idx"
  ON "OrganizationSubscriptions"("planKey", "status");
CREATE INDEX IF NOT EXISTS "OrganizationSubscriptions_status_idx"
  ON "OrganizationSubscriptions"("status");

CREATE TABLE IF NOT EXISTS "CreditWallets" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "balance" INTEGER NOT NULL DEFAULT 0,
  "reserved" INTEGER NOT NULL DEFAULT 0,
  "lifetimeGranted" INTEGER NOT NULL DEFAULT 0,
  "lifetimeSpent" INTEGER NOT NULL DEFAULT 0,
  "currency" TEXT NOT NULL DEFAULT 'credits',
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CreditWallets_organizationId_idx" ON "CreditWallets"("organizationId");
CREATE INDEX IF NOT EXISTS "CreditWallets_workspaceId_idx" ON "CreditWallets"("workspaceId");

CREATE TABLE IF NOT EXISTS "CreditTransactions" (
  "id" TEXT PRIMARY KEY,
  "walletId" TEXT NOT NULL,
  "organizationId" TEXT NOT NULL,
  "amount" INTEGER NOT NULL,
  "balanceAfter" INTEGER NOT NULL,
  "txnType" TEXT NOT NULL,
  "reason" TEXT NOT NULL DEFAULT '',
  "actorId" TEXT,
  "workspaceId" TEXT,
  "referenceType" TEXT,
  "referenceId" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "CreditTransactions_organizationId_createdAt_idx"
  ON "CreditTransactions"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CreditTransactions_walletId_createdAt_idx"
  ON "CreditTransactions"("walletId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "CreditTransactions_actorId_idx" ON "CreditTransactions"("actorId");

CREATE TABLE IF NOT EXISTS "UsageRecords" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "workspaceId" TEXT,
  "userId" TEXT,
  "usageType" TEXT NOT NULL,
  "quantity" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "creditsConsumed" INTEGER NOT NULL DEFAULT 0,
  "provider" TEXT,
  "resourceType" TEXT,
  "resourceId" TEXT,
  "metadataJson" JSONB,
  "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "UsageRecords_organizationId_recordedAt_idx"
  ON "UsageRecords"("organizationId", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "UsageRecords_workspaceId_recordedAt_idx"
  ON "UsageRecords"("workspaceId", "recordedAt" DESC);
CREATE INDEX IF NOT EXISTS "UsageRecords_usageType_idx" ON "UsageRecords"("usageType");
CREATE INDEX IF NOT EXISTS "UsageRecords_userId_idx" ON "UsageRecords"("userId");

CREATE TABLE IF NOT EXISTS "BillingProfiles" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL UNIQUE,
  "companyName" TEXT NOT NULL DEFAULT '',
  "billingEmail" TEXT NOT NULL DEFAULT '',
  "country" TEXT NOT NULL DEFAULT '',
  "taxId" TEXT,
  "addressLine1" TEXT,
  "addressLine2" TEXT,
  "city" TEXT,
  "state" TEXT,
  "postalCode" TEXT,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Invoices" (
  "id" TEXT PRIMARY KEY,
  "organizationId" TEXT NOT NULL,
  "subscriptionId" TEXT,
  "invoiceNumber" TEXT NOT NULL UNIQUE,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "subtotalUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "taxUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "totalUsd" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "billingCycle" TEXT NOT NULL DEFAULT 'monthly',
  "planKey" TEXT,
  "periodStart" TIMESTAMP(3),
  "periodEnd" TIMESTAMP(3),
  "issuedAt" TIMESTAMP(3),
  "dueAt" TIMESTAMP(3),
  "paidAt" TIMESTAMP(3),
  "lineItemsJson" JSONB,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Invoices_organizationId_createdAt_idx"
  ON "Invoices"("organizationId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS "Invoices_subscriptionId_idx" ON "Invoices"("subscriptionId");
CREATE INDEX IF NOT EXISTS "Invoices_status_idx" ON "Invoices"("status");
