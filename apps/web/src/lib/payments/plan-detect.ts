import {

  PREMIUM_MONTHLY_CREDITS,

  STANDARD_MONTHLY_CREDITS,

  TESTER_PLAN_CREDITS,

  TESTER_PLAN_DAYS,

  type PaidPlanType,

} from "@rtas/shared";



export function resolvePlanFromCustomData(

  custom: Record<string, string> | undefined

): PaidPlanType {

  const plan = (custom?.plan ?? custom?.plan_type ?? custom?.planType ?? "")

    .toLowerCase()

    .trim();

  if (plan === "tester") return "tester";

  if (plan === "premium") return "premium";

  if (plan === "standard") return "standard";

  return "standard";

}



export function resolvePlanFromVariantId(

  variantOrPriceId: string | number | undefined

): PaidPlanType | null {

  if (variantOrPriceId === undefined || variantOrPriceId === "") return null;

  const id = String(variantOrPriceId);

  const testerIds = [

    process.env.PADDLE_TESTER_PRICE_ID,

    process.env.LEMONSQUEEZY_TESTER_VARIANT_ID,

  ]

    .filter(Boolean)

    .map((v) => String(v));

  const premiumIds = [

    process.env.PADDLE_PREMIUM_PRICE_ID,

    process.env.LEMONSQUEEZY_PREMIUM_VARIANT_ID,

  ]

    .filter(Boolean)

    .map((v) => String(v));

  if (testerIds.includes(id)) return "tester";

  if (premiumIds.includes(id)) return "premium";

  return "standard";

}



export function creditsForPlan(plan: PaidPlanType): number {

  if (plan === "tester") return TESTER_PLAN_CREDITS;

  if (plan === "premium") return PREMIUM_MONTHLY_CREDITS;

  return STANDARD_MONTHLY_CREDITS;

}



export function billingEndForPlan(plan: PaidPlanType, providerEnd?: string): string {

  if (providerEnd) return providerEnd;

  const end = new Date();

  if (plan === "tester") {

    end.setDate(end.getDate() + TESTER_PLAN_DAYS);

  } else {

    end.setMonth(end.getMonth() + 1);

  }

  return end.toISOString();

}


