/**
 * Phase 13 Sprint 2 — Server helpers for enterprise CRM persistence.
 */

import { createHash, randomUUID } from "crypto";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import {
  ENTERPRISE_DEMO_TYPES,
  ENTERPRISE_PIPELINE_STAGES,
  ENTERPRISE_PLAN_INTERESTS,
  ENTERPRISE_PRIORITIES,
  ENTERPRISE_REQUEST_TYPES,
  DEMO_STAGES,
  OPEN_PIPELINE_STAGES,
  QUALIFIED_STAGES,
  stageImpliesStatus,
  type EnterpriseDemoType,
  type EnterprisePipelineStage,
  type EnterprisePlanInterest,
  type EnterprisePriority,
  type EnterpriseRequestType,
} from "@/lib/enterprise/pipeline";

export type CreateLeadInput = {
  kind: string;
  name: string;
  email: string;
  company?: string;
  role?: string;
  website?: string;
  phone?: string;
  teamSize?: string;
  industry?: string;
  requestType?: string;
  demoType?: string;
  message?: string;
  planInterest?: string;
  timeline?: string;
  requirements?: string;
  source?: string;
  ip?: string;
  userAgent?: string;
};

function hashIp(ip: string | undefined): string | undefined {
  if (!ip || ip === "unknown") return undefined;
  return createHash("sha256").update(ip).digest("hex").slice(0, 32);
}

function normalizeDemoType(
  requestType: string | undefined,
  demoType: string | undefined
): string | undefined {
  if (demoType && (ENTERPRISE_DEMO_TYPES as readonly string[]).includes(demoType)) {
    return demoType;
  }
  if (requestType === "demo") return "book_demo";
  if (requestType === "technical_consultation") return "technical_consultation";
  if (requestType === "discovery_call") return "discovery_call";
  return undefined;
}

function initialStage(requestType: string | undefined): EnterprisePipelineStage {
  if (
    requestType === "demo" ||
    requestType === "technical_consultation" ||
    requestType === "discovery_call"
  ) {
    return "demo_scheduled";
  }
  return "new_lead";
}

export async function createEnterpriseLead(input: CreateLeadInput): Promise<{
  ok: boolean;
  id?: string;
  skipped?: boolean;
  error?: string;
}> {
  if (!isPrismaConfigured()) {
    return { ok: false, skipped: true, error: "Database not configured." };
  }

  const stage = initialStage(input.requestType);
  const demoType = normalizeDemoType(input.requestType, input.demoType);
  const id = randomUUID();

  try {
    await prisma.enterpriseLead.create({
      data: {
        id,
        kind: input.kind,
        name: input.name,
        email: input.email,
        company: input.company || null,
        role: input.role || null,
        website: input.website || null,
        phone: input.phone || null,
        teamSize: input.teamSize || null,
        industry: input.industry || null,
        requestType: input.requestType || null,
        demoType: demoType || null,
        message: input.message || null,
        planInterest: input.planInterest || null,
        timeline: input.timeline || null,
        requirements: input.requirements || input.message || null,
        stage,
        status: stageImpliesStatus(stage),
        priority: "medium",
        source: input.source || "web_form",
        ipHash: hashIp(input.ip),
        userAgent: input.userAgent?.slice(0, 400) || null,
        activities: {
          create: {
            id: randomUUID(),
            type: demoType ? "demo_booked" : "created",
            body: demoType
              ? `Demo request received (${demoType}). Stage set to ${stage}.`
              : `Lead created from ${input.source || "web_form"}. Stage: ${stage}.`,
            actor: "system",
          },
        },
      },
    });
    return { ok: true, id };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Failed to persist lead.",
    };
  }
}

export type EnterpriseCrmFilters = {
  q?: string;
  stage?: string;
  status?: string;
  priority?: string;
  owner?: string;
  tag?: string;
  limit?: number;
  offset?: number;
};

export async function listEnterpriseLeads(filters: EnterpriseCrmFilters = {}) {
  if (!isPrismaConfigured()) {
    return { leads: [], total: 0, dbConfigured: false as const };
  }

  const where: Record<string, unknown> = {};
  if (filters.stage) where.stage = filters.stage;
  if (filters.status) where.status = filters.status;
  if (filters.priority) where.priority = filters.priority;
  if (filters.owner) where.owner = filters.owner;
  if (filters.tag) where.tags = { contains: filters.tag, mode: "insensitive" };
  if (filters.q?.trim()) {
    const q = filters.q.trim();
    where.OR = [
      { name: { contains: q, mode: "insensitive" } },
      { email: { contains: q, mode: "insensitive" } },
      { company: { contains: q, mode: "insensitive" } },
      { notes: { contains: q, mode: "insensitive" } },
    ];
  }

  const take = Math.min(Math.max(filters.limit ?? 50, 1), 200);
  const skip = Math.max(filters.offset ?? 0, 0);

  const [leads, total] = await Promise.all([
    prisma.enterpriseLead.findMany({
      where,
      orderBy: { createdAt: "desc" },
      take,
      skip,
      include: {
        activities: { orderBy: { createdAt: "desc" }, take: 8 },
        proposals: { orderBy: { createdAt: "desc" }, take: 3 },
      },
    }),
    prisma.enterpriseLead.count({ where }),
  ]);

  return { leads, total, dbConfigured: true as const };
}

export type EnterpriseDashboardMetrics = {
  totalLeads: number;
  qualifiedLeads: number;
  openDeals: number;
  pipelineValueUsd: number;
  demos: number;
  conversionRatePct: number;
  forecastUsd: number;
  closedWon: number;
  closedLost: number;
  byStage: Array<{ stage: string; count: number }>;
};

export async function getEnterpriseDashboardMetrics(): Promise<
  EnterpriseDashboardMetrics & { dbConfigured: boolean }
> {
  const empty: EnterpriseDashboardMetrics & { dbConfigured: boolean } = {
    totalLeads: 0,
    qualifiedLeads: 0,
    openDeals: 0,
    pipelineValueUsd: 0,
    demos: 0,
    conversionRatePct: 0,
    forecastUsd: 0,
    closedWon: 0,
    closedLost: 0,
    byStage: ENTERPRISE_PIPELINE_STAGES.map((stage) => ({ stage, count: 0 })),
    dbConfigured: false,
  };

  if (!isPrismaConfigured()) return empty;

  type LeadMetricRow = {
    stage: string;
    status: string;
    estimatedValueUsd: number | null;
    demoType: string | null;
    requestType: string | null;
  };

  const leads = (await prisma.enterpriseLead.findMany({
    select: {
      stage: true,
      status: true,
      estimatedValueUsd: true,
      demoType: true,
      requestType: true,
    },
  })) as LeadMetricRow[];

  const totalLeads = leads.length;
  const qualifiedLeads = leads.filter((l: LeadMetricRow) =>
    QUALIFIED_STAGES.includes(l.stage as EnterprisePipelineStage)
  ).length;
  const openDeals = leads.filter((l: LeadMetricRow) =>
    OPEN_PIPELINE_STAGES.includes(l.stage as EnterprisePipelineStage)
  ).length;
  const closedWon = leads.filter((l: LeadMetricRow) => l.stage === "closed_won").length;
  const closedLost = leads.filter((l: LeadMetricRow) => l.stage === "closed_lost").length;
  const demos = leads.filter(
    (l: LeadMetricRow) =>
      DEMO_STAGES.includes(l.stage as EnterprisePipelineStage) ||
      Boolean(l.demoType) ||
      l.requestType === "demo" ||
      l.requestType === "technical_consultation" ||
      l.requestType === "discovery_call"
  ).length;

  const openWithValue = leads.filter((l: LeadMetricRow) =>
    OPEN_PIPELINE_STAGES.includes(l.stage as EnterprisePipelineStage)
  );
  const pipelineValueUsd = openWithValue.reduce(
    (sum: number, l: LeadMetricRow) =>
      sum + (typeof l.estimatedValueUsd === "number" ? l.estimatedValueUsd : 0),
    0
  );
  // Forecast = open pipeline value only (no invented multipliers)
  const forecastUsd = pipelineValueUsd;

  const decided = closedWon + closedLost;
  const conversionRatePct =
    decided > 0 ? Math.round((closedWon / decided) * 1000) / 10 : 0;

  const byStage = ENTERPRISE_PIPELINE_STAGES.map((stage) => ({
    stage,
    count: leads.filter((l: LeadMetricRow) => l.stage === stage).length,
  }));

  return {
    totalLeads,
    qualifiedLeads,
    openDeals,
    pipelineValueUsd,
    demos,
    conversionRatePct,
    forecastUsd,
    closedWon,
    closedLost,
    byStage,
    dbConfigured: true,
  };
}

export async function updateEnterpriseLead(
  id: string,
  patch: {
    stage?: string;
    status?: string;
    priority?: string;
    owner?: string | null;
    notes?: string | null;
    tags?: string;
    estimatedValueUsd?: number | null;
    lossReason?: string | null;
    forecastCloseAt?: string | null;
    actor?: string;
  }
) {
  if (!isPrismaConfigured()) {
    return { ok: false as const, error: "Database not configured." };
  }

  const existing = await prisma.enterpriseLead.findUnique({ where: { id } });
  if (!existing) return { ok: false as const, error: "Lead not found." };

  const data: Record<string, unknown> = {};
  const activities: Array<{ type: string; body: string }> = [];
  const actor = patch.actor || "admin";

  if (patch.stage && (ENTERPRISE_PIPELINE_STAGES as readonly string[]).includes(patch.stage)) {
    data.stage = patch.stage;
    data.status = stageImpliesStatus(patch.stage as EnterprisePipelineStage);
    if (patch.stage !== existing.stage) {
      activities.push({
        type: "stage_change",
        body: `Stage: ${existing.stage} → ${patch.stage}`,
      });
    }
  }
  if (patch.status && patch.status !== existing.status) {
    data.status = patch.status;
    activities.push({
      type: "status_change",
      body: `Status: ${existing.status} → ${patch.status}`,
    });
  }
  if (
    patch.priority &&
    (ENTERPRISE_PRIORITIES as readonly string[]).includes(patch.priority) &&
    patch.priority !== existing.priority
  ) {
    data.priority = patch.priority;
    activities.push({
      type: "priority_change",
      body: `Priority: ${existing.priority} → ${patch.priority}`,
    });
  }
  if (patch.owner !== undefined && patch.owner !== existing.owner) {
    data.owner = patch.owner;
    activities.push({
      type: "owner_change",
      body: `Owner: ${existing.owner || "(unassigned)"} → ${patch.owner || "(unassigned)"}`,
    });
  }
  if (patch.notes !== undefined) {
    data.notes = patch.notes;
    if (patch.notes && patch.notes !== existing.notes) {
      activities.push({ type: "note", body: patch.notes.slice(0, 2000) });
    }
  }
  if (patch.tags !== undefined && patch.tags !== existing.tags) {
    data.tags = patch.tags;
    activities.push({ type: "tag", body: `Tags updated: ${patch.tags || "(none)"}` });
  }
  if (patch.estimatedValueUsd !== undefined) {
    data.estimatedValueUsd = patch.estimatedValueUsd;
  }
  if (patch.lossReason !== undefined) data.lossReason = patch.lossReason;
  if (patch.forecastCloseAt !== undefined) {
    data.forecastCloseAt = patch.forecastCloseAt
      ? new Date(patch.forecastCloseAt)
      : null;
  }

  const updated = await prisma.enterpriseLead.update({
    where: { id },
    data: {
      ...data,
      ...(activities.length
        ? {
            activities: {
              create: activities.map((a) => ({
                id: randomUUID(),
                type: a.type,
                body: a.body,
                actor,
              })),
            },
          }
        : {}),
    },
    include: {
      activities: { orderBy: { createdAt: "desc" }, take: 20 },
      proposals: { orderBy: { createdAt: "desc" }, take: 5 },
    },
  });

  return { ok: true as const, lead: updated };
}

export async function addEnterpriseLeadNote(
  id: string,
  body: string,
  actor = "admin"
) {
  if (!isPrismaConfigured()) {
    return { ok: false as const, error: "Database not configured." };
  }
  const existing = await prisma.enterpriseLead.findUnique({ where: { id } });
  if (!existing) return { ok: false as const, error: "Lead not found." };

  await prisma.enterpriseLeadActivity.create({
    data: {
      id: randomUUID(),
      leadId: id,
      type: "note",
      body: body.slice(0, 4000),
      actor,
    },
  });

  const lead = await prisma.enterpriseLead.findUnique({
    where: { id },
    include: {
      activities: { orderBy: { createdAt: "desc" }, take: 20 },
      proposals: { orderBy: { createdAt: "desc" }, take: 5 },
    },
  });
  return { ok: true as const, lead };
}

export function isValidPlanInterest(v: string): v is EnterprisePlanInterest {
  return (ENTERPRISE_PLAN_INTERESTS as readonly string[]).includes(v);
}

export function isValidRequestType(v: string): v is EnterpriseRequestType {
  return (ENTERPRISE_REQUEST_TYPES as readonly string[]).includes(v);
}

export function isValidDemoType(v: string): v is EnterpriseDemoType {
  return (ENTERPRISE_DEMO_TYPES as readonly string[]).includes(v);
}

export function isValidPriority(v: string): v is EnterprisePriority {
  return (ENTERPRISE_PRIORITIES as readonly string[]).includes(v);
}
