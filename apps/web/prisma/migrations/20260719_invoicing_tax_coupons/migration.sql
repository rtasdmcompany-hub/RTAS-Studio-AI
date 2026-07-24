-- No-op migration: directory previously lacked migration.sql (Prisma P3015).
-- Invoicing/tax/coupon schema is covered by adjacent billing migrations
-- (e.g. 20260719_billing_automation_invoicing). Keep history intact.
SELECT 1;
