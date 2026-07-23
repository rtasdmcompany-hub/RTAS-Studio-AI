CREATE TABLE "RevenuePromotions" (
  "id" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT NOT NULL DEFAULT '',
  "promotionType" TEXT NOT NULL,
  "sponsorName" TEXT,
  "sponsorLabel" TEXT,
  "status" TEXT NOT NULL DEFAULT 'draft',
  "targetPage" TEXT NOT NULL DEFAULT '*',
  "placements" TEXT[] DEFAULT ARRAY[]::TEXT[],
  "audienceRules" JSONB,
  "variants" JSONB,
  "ctaLabel" TEXT NOT NULL DEFAULT 'Learn more',
  "ctaHref" TEXT NOT NULL,
  "ctaKind" TEXT NOT NULL DEFAULT 'link',
  "checkoutPlan" TEXT,
  "imageUrl" TEXT,
  "badgeText" TEXT,
  "priority" INTEGER NOT NULL DEFAULT 100,
  "dismissible" BOOLEAN NOT NULL DEFAULT true,
  "revenueValueCents" INTEGER NOT NULL DEFAULT 0,
  "startAt" TIMESTAMP(3),
  "endAt" TIMESTAMP(3),
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RevenuePromotions_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "RevenuePromotionInteractions" (
  "id" TEXT NOT NULL,
  "promotionId" TEXT NOT NULL,
  "variantId" TEXT,
  "action" TEXT NOT NULL,
  "placement" TEXT NOT NULL,
  "pagePath" TEXT NOT NULL,
  "userId" TEXT,
  "sessionId" TEXT,
  "country" TEXT,
  "language" TEXT,
  "revenueAmountCents" INTEGER NOT NULL DEFAULT 0,
  "metadataJson" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "RevenuePromotionInteractions_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "RevenuePromotions_slug_key" ON "RevenuePromotions"("slug");
CREATE INDEX "RevenuePromotions_status_priority_idx" ON "RevenuePromotions"("status", "priority");
CREATE INDEX "RevenuePromotions_targetPage_idx" ON "RevenuePromotions"("targetPage");
CREATE INDEX "RevenuePromotions_promotionType_status_idx" ON "RevenuePromotions"("promotionType", "status");
CREATE INDEX "RevenuePromotionInteractions_promotionId_action_createdAt_idx" ON "RevenuePromotionInteractions"("promotionId", "action", "createdAt" DESC);
CREATE INDEX "RevenuePromotionInteractions_placement_createdAt_idx" ON "RevenuePromotionInteractions"("placement", "createdAt" DESC);
CREATE INDEX "RevenuePromotionInteractions_pagePath_createdAt_idx" ON "RevenuePromotionInteractions"("pagePath", "createdAt" DESC);
CREATE INDEX "RevenuePromotionInteractions_userId_createdAt_idx" ON "RevenuePromotionInteractions"("userId", "createdAt" DESC);

ALTER TABLE "RevenuePromotionInteractions"
ADD CONSTRAINT "RevenuePromotionInteractions_promotionId_fkey"
FOREIGN KEY ("promotionId") REFERENCES "RevenuePromotions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

INSERT INTO "RevenuePromotions" (
  "id",
  "slug",
  "title",
  "description",
  "promotionType",
  "status",
  "targetPage",
  "placements",
  "audienceRules",
  "variants",
  "ctaLabel",
  "ctaHref",
  "ctaKind",
  "badgeText",
  "priority",
  "dismissible",
  "revenueValueCents",
  "metadataJson"
) VALUES
(
  '11111111-1111-4111-8111-111111111111',
  'standard-upgrade-push',
  'Unlock HD exports with Standard',
  'Move from evaluation to commercial-ready rendering with monthly credits, HD output, and queue priority.',
  'internal',
  'active',
  '*',
  ARRAY['dashboard_sidebar','billing_upgrade','credits_upgrade','studio_recommendations'],
  '{"audiences":["free_user"],"plans":["free"],"maxCredits":30}',
  '[{"id":"control","headline":"Unlock HD exports with Standard","body":"Monthly credits, commercial downloads, and faster weekly output.","ctaLabel":"View upgrade options"},{"id":"value","headline":"Keep creating without credit stalls","body":"Standard gives you predictable monthly capacity for recurring work.","ctaLabel":"Compare Standard"}]',
  'View upgrade options',
  '/pricing',
  'link',
  'Internal',
  10,
  true,
  8900,
  '{"theme":"lavender","campaign":"phase13-rpe"}'
),
(
  '22222222-2222-4222-8222-222222222222',
  'enterprise-cta-priority',
  'Need procurement, teams, or white label?',
  'RTAS Studio AI Enterprise supports proposal-based commercial terms, team workflows, and deployment discussions.',
  'internal',
  'active',
  '/enterprise',
  ARRAY['enterprise_cta','dashboard_sidebar'],
  '{"audiences":["paid_user","enterprise_lead","free_user"]}',
  '[{"id":"control","headline":"Need procurement, teams, or white label?","body":"Talk to RTAS sales about enterprise workflows, deployment, and white-label scoping.","ctaLabel":"Contact enterprise sales"}]',
  'Contact enterprise sales',
  '/enterprise#contact',
  'link',
  'Enterprise',
  20,
  true,
  0,
  '{"theme":"glass","campaign":"phase13-rpe"}'
),
(
  '33333333-3333-4333-8333-333333333333',
  'docs-learning-path',
  'Learn faster with the RTAS Success Center',
  'Tutorials, best practices, release notes, and workflow guides in one premium knowledge surface.',
  'educational',
  'active',
  '*',
  ARRAY['docs_partner_recommendations','learning_center'],
  '{"languages":["en"],"recentActivity":["inactive_14d","no_generation_30d"]}',
  '[{"id":"control","headline":"Learn faster with the RTAS Success Center","body":"Go from first render to repeatable workflow with curated docs and tutorials.","ctaLabel":"Open learning center"}]',
  'Open learning center',
  '/success',
  'link',
  'Education',
  30,
  true,
  0,
  '{"theme":"emerald","campaign":"phase13-rpe"}'
);
