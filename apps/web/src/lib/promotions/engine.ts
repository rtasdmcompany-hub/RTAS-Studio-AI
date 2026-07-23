import { randomUUID } from "crypto";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { getServerProfile } from "@/lib/server/profile-store";
import { trackServerEvent } from "@/lib/analytics";
import { AnalyticsEvents } from "@/lib/analytics/events";
import type {
  PromotionAction,
  PromotionAdminRow,
  PromotionAudienceRules,
  PromotionMetrics,
  PromotionRecord,
  PromotionResolved,
  PromotionVariant,
  PromotionViewerContext,
} from "./types";

type PromotionRowRaw = Awaited<
  ReturnType<typeof prisma.revenuePromotion.findMany>
>[number];

type InteractionAggregate = Awaited<
  ReturnType<typeof prisma.revenuePromotionInteraction.findMany>
>[number];

function safeObject(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function safeAudienceRules(value: unknown): PromotionAudienceRules | null {
  const obj = safeObject(value);
  if (!obj) return null;
  return obj as PromotionAudienceRules;
}

function safeVariants(value: unknown): PromotionVariant[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === "object")
    .map((item, index) => {
      const row = item as Record<string, unknown>;
      return {
        id: String(row.id ?? `variant-${index + 1}`),
        headline: typeof row.headline === "string" ? row.headline : undefined,
        body: typeof row.body === "string" ? row.body : undefined,
        ctaLabel: typeof row.ctaLabel === "string" ? row.ctaLabel : undefined,
        imageUrl: typeof row.imageUrl === "string" ? row.imageUrl : undefined,
        placement: typeof row.placement === "string" ? row.placement : undefined,
        audienceOverrides: safeAudienceRules(row.audienceOverrides),
      };
    });
}

function toPromotionRecord(row: PromotionRowRaw): PromotionRecord {
  return {
    id: row.id,
    slug: row.slug,
    title: row.title,
    description: row.description,
    promotionType: row.promotionType as PromotionRecord["promotionType"],
    sponsorName: row.sponsorName,
    sponsorLabel: row.sponsorLabel,
    status: row.status as PromotionRecord["status"],
    targetPage: row.targetPage,
    placements: row.placements,
    audienceRules: safeAudienceRules(row.audienceRules),
    variants: safeVariants(row.variants),
    ctaLabel: row.ctaLabel,
    ctaHref: row.ctaHref,
    ctaKind: row.ctaKind === "checkout" ? "checkout" : "link",
    checkoutPlan:
      row.checkoutPlan === "tester" ||
      row.checkoutPlan === "standard" ||
      row.checkoutPlan === "premium"
        ? row.checkoutPlan
        : null,
    imageUrl: row.imageUrl,
    badgeText: row.badgeText,
    priority: row.priority,
    dismissible: row.dismissible,
    revenueValueCents: row.revenueValueCents,
    startAt: row.startAt?.toISOString() ?? null,
    endAt: row.endAt?.toISOString() ?? null,
    metadataJson: safeObject(row.metadataJson),
    createdAt: row.createdAt.toISOString(),
    updatedAt: row.updatedAt.toISOString(),
  };
}

function normalizePath(path: string): string {
  const value = (path || "/").trim();
  if (!value) return "/";
  return value.startsWith("/") ? value : `/${value}`;
}

function pathMatches(targetPage: string, pagePath: string): boolean {
  const target = normalizePath(targetPage);
  const page = normalizePath(pagePath);
  if (target === "*" || target === "/*") return true;
  if (target.endsWith("*")) {
    return page.startsWith(target.slice(0, -1));
  }
  return page === target;
}

function hashString(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 31 + input.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

function matchesAudienceRules(
  rules: PromotionAudienceRules | null | undefined,
  context: PromotionViewerContext
): boolean {
  if (!rules) return true;
  if (rules.audiences?.length && !rules.audiences.includes(context.audience)) {
    return false;
  }
  if (rules.countries?.length) {
    const match = rules.countries.some(
      (country) => country.toLowerCase() === context.country.toLowerCase()
    );
    if (!match) return false;
  }
  if (rules.languages?.length) {
    const language = context.language.toLowerCase();
    const match = rules.languages.some((item) => language.startsWith(item.toLowerCase()));
    if (!match) return false;
  }
  if (rules.plans?.length && !rules.plans.includes(context.plan)) {
    return false;
  }
  if (typeof rules.minCredits === "number" && context.credits < rules.minCredits) {
    return false;
  }
  if (typeof rules.maxCredits === "number" && context.credits > rules.maxCredits) {
    return false;
  }
  if (rules.recentActivity?.length) {
    for (const key of rules.recentActivity) {
      if (key === "active_last_7d" && !context.recentActivity.activeLast7d) return false;
      if (key === "inactive_14d" && !context.recentActivity.inactive14d) return false;
      if (key === "generated_last_30d" && !context.recentActivity.generatedLast30d) {
        return false;
      }
      if (key === "no_generation_30d" && !context.recentActivity.noGeneration30d) {
        return false;
      }
    }
  }
  return true;
}

function chooseVariant(
  promotion: PromotionRecord,
  placement: string,
  context: PromotionViewerContext
): PromotionVariant | null {
  const eligible = promotion.variants.filter((variant) => {
    if (variant.placement && variant.placement !== placement) return false;
    return matchesAudienceRules(variant.audienceOverrides, context);
  });
  if (eligible.length === 0) return null;
  const seed = `${promotion.id}:${context.userId ?? context.sessionId}:${placement}`;
  return eligible[hashString(seed) % eligible.length] ?? eligible[0] ?? null;
}

async function getEnterpriseLeadFlag(userId?: string): Promise<boolean> {
  if (!userId || !isPrismaConfigured()) return false;
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { email: true },
  });
  if (!user?.email) return false;
  const emailCount = await prisma.commercialLead.count({
    where: {
      email: user.email,
      OR: [{ kind: "enterprise" }, { kind: "partner" }],
    },
  }).catch(() => 0);
  return emailCount > 0;
}

export async function buildPromotionViewerContext(input: {
  userId?: string;
  sessionId?: string;
  country?: string | null;
  language?: string | null;
}): Promise<PromotionViewerContext> {
  const sessionId = input.sessionId?.trim() || randomUUID();
  const country = (input.country || "global").trim().toLowerCase() || "global";
  const language = (input.language || "en").trim().toLowerCase() || "en";
  let audience: PromotionViewerContext["audience"] = "free_user";
  let plan = "free";
  let credits = 0;
  let activeLast7d = false;
  let inactive14d = true;
  let generatedLast30d = false;
  let noGeneration30d = true;

  if (input.userId) {
    const profile = await getServerProfile(input.userId);
    audience =
      profile.subscriptionActive || ["tester", "standard", "premium"].includes(profile.tier)
        ? "paid_user"
        : "free_user";
    plan = profile.tier || "free";
    credits = profile.credits ?? 0;

    if (isPrismaConfigured()) {
      const latestJob = await prisma.generationJob.findFirst({
        where: { userId: input.userId },
        orderBy: { createdAt: "desc" },
        select: { createdAt: true },
      }).catch(() => null);
      if (latestJob?.createdAt) {
        const jobDaysAgo = (Date.now() - latestJob.createdAt.getTime()) / 86_400_000;
        activeLast7d = jobDaysAgo <= 7;
        inactive14d = jobDaysAgo >= 14;
        generatedLast30d = jobDaysAgo <= 30;
        noGeneration30d = jobDaysAgo > 30;
      }
    }

    if (await getEnterpriseLeadFlag(input.userId)) {
      audience = "enterprise_lead";
    }
  }

  return {
    userId: input.userId,
    sessionId,
    audience,
    plan,
    credits,
    country,
    language,
    recentActivity: {
      activeLast7d,
      inactive14d,
      generatedLast30d,
      noGeneration30d,
    },
  };
}

export async function resolvePromotionsForPlacement(input: {
  placement: string;
  pagePath: string;
  userId?: string;
  sessionId?: string;
  country?: string | null;
  language?: string | null;
}): Promise<{ context: PromotionViewerContext; promotions: PromotionResolved[] }> {
  const context = await buildPromotionViewerContext(input);
  if (!isPrismaConfigured()) {
    return { context, promotions: [] };
  }

  const now = new Date();
  const rows = await prisma.revenuePromotion.findMany({
    where: {
      status: "active",
      placements: { has: input.placement },
      OR: [{ startAt: null }, { startAt: { lte: now } }],
      AND: [{ OR: [{ endAt: null }, { endAt: { gte: now } }] }],
    },
    orderBy: [{ priority: "asc" }, { updatedAt: "desc" }],
  });

  const promotions = rows
    .map(toPromotionRecord)
    .filter((promotion) => pathMatches(promotion.targetPage, input.pagePath))
    .filter((promotion) => matchesAudienceRules(promotion.audienceRules, context))
    .map((promotion) => ({
      promotion,
      variant: chooseVariant(promotion, input.placement, context),
      placement: input.placement,
      pagePath: normalizePath(input.pagePath),
    }));

  const limit = input.placement === "homepage_announcement" ? 1 : 2;
  return { context, promotions: promotions.slice(0, limit) };
}

export async function recordPromotionInteraction(input: {
  promotionId: string;
  variantId?: string | null;
  action: PromotionAction;
  placement: string;
  pagePath: string;
  userId?: string;
  sessionId?: string;
  country?: string | null;
  language?: string | null;
  revenueAmountCents?: number;
  metadataJson?: Record<string, unknown>;
}): Promise<void> {
  if (!isPrismaConfigured()) return;
  await prisma.revenuePromotionInteraction.create({
    data: {
      promotionId: input.promotionId,
      variantId: input.variantId ?? null,
      action: input.action,
      placement: input.placement,
      pagePath: normalizePath(input.pagePath),
      userId: input.userId,
      sessionId: input.sessionId ?? null,
      country: input.country?.toLowerCase() ?? null,
      language: input.language?.toLowerCase() ?? null,
      revenueAmountCents: Math.max(0, Math.round(input.revenueAmountCents ?? 0)),
      metadataJson: input.metadataJson ?? undefined,
    },
  });

  trackServerEvent(AnalyticsEvents.LIFECYCLE_STAGE, {
    feature: "promotion_engine",
    action: input.action,
    placement: input.placement,
    promotionId: input.promotionId,
  });
}

function computeMetrics(rows: InteractionAggregate[]): PromotionMetrics {
  const views = rows.filter((row) => row.action === "view").length;
  const clicks = rows.filter((row) => row.action === "click").length;
  const dismisses = rows.filter((row) => row.action === "dismiss").length;
  const conversions = rows.filter((row) => row.action === "conversion").length;
  const revenueGeneratedUsd =
    rows.reduce((sum, row) => sum + (row.revenueAmountCents ?? 0), 0) / 100;

  return {
    views,
    clicks,
    ctr: views > 0 ? Number(((clicks / views) * 100).toFixed(2)) : 0,
    dismisses,
    dismissRate: views > 0 ? Number(((dismisses / views) * 100).toFixed(2)) : 0,
    conversions,
    revenueGeneratedUsd: Number(revenueGeneratedUsd.toFixed(2)),
  };
}

export async function listPromotionAdminRows(): Promise<PromotionAdminRow[]> {
  if (!isPrismaConfigured()) return [];
  const [promotions, interactions] = await Promise.all([
    prisma.revenuePromotion.findMany({
      orderBy: [{ priority: "asc" }, { updatedAt: "desc" }],
    }),
    prisma.revenuePromotionInteraction.findMany({
      orderBy: { createdAt: "desc" },
      take: 5000,
    }),
  ]);

  return promotions.map((row) => {
    const promotion = toPromotionRecord(row);
    const metrics = computeMetrics(
      interactions.filter((interaction) => interaction.promotionId === row.id)
    );
    return { ...promotion, metrics };
  });
}

function splitCsv(value: string | undefined): string[] {
  return (value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseJson<T>(value: string | undefined, fallback: T): T {
  if (!value?.trim()) return fallback;
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

export async function savePromotionFromAdmin(input: Record<string, string>) {
  if (!isPrismaConfigured()) {
    throw new Error("Prisma is not configured for promotions.");
  }

  const now = new Date();
  const title = input.title?.trim();
  const ctaHref = input.ctaHref?.trim();
  if (!title) throw new Error("Promotion title is required.");
  if (!ctaHref) throw new Error("Promotion CTA link is required.");

  const slug =
    input.slug?.trim() ||
    title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") ||
    `promotion-${Date.now()}`;

  const data = {
    slug,
    title,
    description: input.description?.trim() || "",
    promotionType: input.promotionType?.trim() || "internal",
    sponsorName: input.sponsorName?.trim() || null,
    sponsorLabel: input.sponsorLabel?.trim() || null,
    status: input.status?.trim() || "draft",
    targetPage: normalizePath(input.targetPage?.trim() || "*"),
    placements: splitCsv(input.placements),
    audienceRules: parseJson<PromotionAudienceRules | null>(input.audienceRules, null),
    variants: parseJson<PromotionVariant[]>(input.variants, []),
    ctaLabel: input.ctaLabel?.trim() || "Learn more",
    ctaHref,
    ctaKind: input.ctaKind === "checkout" ? "checkout" : "link",
    checkoutPlan:
      input.checkoutPlan === "tester" ||
      input.checkoutPlan === "standard" ||
      input.checkoutPlan === "premium"
        ? input.checkoutPlan
        : null,
    imageUrl: input.imageUrl?.trim() || null,
    badgeText: input.badgeText?.trim() || null,
    priority: Number(input.priority ?? "100") || 100,
    dismissible: input.dismissible !== "false",
    revenueValueCents: Math.max(0, Math.round((Number(input.revenueValueUsd ?? "0") || 0) * 100)),
    startAt: input.startAt ? new Date(input.startAt) : null,
    endAt: input.endAt ? new Date(input.endAt) : null,
    metadataJson: parseJson<Record<string, unknown> | null>(input.metadataJson, {
      updatedAt: now.toISOString(),
    }),
  };

  const id = input.id?.trim();
  const saved = id
    ? await prisma.revenuePromotion.update({
        where: { id },
        data,
      })
    : await prisma.revenuePromotion.create({ data });
  return toPromotionRecord(saved);
}
