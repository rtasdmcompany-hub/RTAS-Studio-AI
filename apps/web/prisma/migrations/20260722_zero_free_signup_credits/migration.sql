-- Product truth: free accounts start at 0 credits.
-- Entry plan is Tester ($5 / 30 seconds / 5 days). There is no free signup grant.
ALTER TABLE "User" ALTER COLUMN "credits" SET DEFAULT 0;

-- Clear the legacy default grant for unpaid free-tier accounts that still hold exactly 50.
UPDATE "User"
SET credits = 0
WHERE tier = 'free'
  AND "subscriptionActive" = false
  AND credits = 50
  AND "paymentProvider" IS NULL;
