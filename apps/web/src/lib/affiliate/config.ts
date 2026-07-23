/**
 * Affiliate & partner program configuration (server-oriented env reads).
 * Payouts are NOT live until AFFILIATE_PAYOUTS_LIVE is explicitly enabled.
 */

export {
  AFFILIATE_COMMISSION_PLACEHOLDER,
  PARTNER_TYPES,
  PARTNER_TYPE_IDS,
  isPartnerTypeId,
  buildReferralUrl,
  generateReferralCode,
  type PartnerTypeId,
} from "./constants";

function readIntEnv(key: string, fallback: number): number {
  const raw = process.env[key]?.trim();
  if (!raw) return fallback;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function readBoolEnv(key: string, fallback: boolean): boolean {
  const raw = process.env[key]?.trim().toLowerCase();
  if (!raw) return fallback;
  if (["1", "true", "yes", "on"].includes(raw)) return true;
  if (["0", "false", "no", "off"].includes(raw)) return false;
  return fallback;
}

/** Cookie / attribution window in days (env: AFFILIATE_COOKIE_DAYS). */
export const AFFILIATE_COOKIE_DAYS = readIntEnv("AFFILIATE_COOKIE_DAYS", 30);

/**
 * Hard gate: public marketing and dashboards must treat commissions as
 * non-payable until this is true AND ops has configured payout rails.
 */
export const AFFILIATE_PAYOUTS_LIVE = readBoolEnv("AFFILIATE_PAYOUTS_LIVE", false);

/** Minimum payout threshold in USD once payouts go live (placeholder). */
export const AFFILIATE_MIN_PAYOUT_USD = readIntEnv("AFFILIATE_MIN_PAYOUT_USD", 50);

/** Net days after month close for payout processing (placeholder). */
export const AFFILIATE_PAYOUT_NET_DAYS = readIntEnv("AFFILIATE_PAYOUT_NET_DAYS", 30);

export const AFFILIATE_PROGRAM_STATUS = AFFILIATE_PAYOUTS_LIVE
  ? ("accepting_with_payouts" as const)
  : ("applications_open_payouts_not_live" as const);
