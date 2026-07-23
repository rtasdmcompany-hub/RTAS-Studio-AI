import { NextResponse } from "next/server";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";
import {
  addEnterpriseLeadNote,
  getEnterpriseDashboardMetrics,
  listEnterpriseLeads,
  updateEnterpriseLead,
} from "@/lib/enterprise/crm";
import {
  isEnterpriseLeadStatus,
  isEnterprisePipelineStage,
  isEnterprisePriority,
  serializeTags,
} from "@/lib/enterprise/pipeline";

export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const url = new URL(request.url);
  const view = url.searchParams.get("view") || "leads";

  if (view === "metrics") {
    const metrics = await getEnterpriseDashboardMetrics();
    return NextResponse.json({ ok: true, metrics });
  }

  const result = await listEnterpriseLeads({
    q: url.searchParams.get("q") || undefined,
    stage: url.searchParams.get("stage") || undefined,
    status: url.searchParams.get("status") || undefined,
    priority: url.searchParams.get("priority") || undefined,
    owner: url.searchParams.get("owner") || undefined,
    tag: url.searchParams.get("tag") || undefined,
    limit: Number(url.searchParams.get("limit") || 50),
    offset: Number(url.searchParams.get("offset") || 0),
  });

  return NextResponse.json({
    ok: true,
    total: result.total,
    dbConfigured: result.dbConfigured,
    leads: result.leads,
  });
}

export async function PATCH(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const id = typeof body.id === "string" ? body.id.trim() : "";
  if (!id) {
    return NextResponse.json({ error: "Lead id is required." }, { status: 400 });
  }

  if (typeof body.note === "string" && body.note.trim()) {
    const result = await addEnterpriseLeadNote(
      id,
      body.note.trim(),
      typeof body.actor === "string" ? body.actor : "admin"
    );
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 404 });
    }
    return NextResponse.json({ ok: true, lead: result.lead });
  }

  const stage = typeof body.stage === "string" ? body.stage : undefined;
  const status = typeof body.status === "string" ? body.status : undefined;
  const priority = typeof body.priority === "string" ? body.priority : undefined;

  if (stage && !isEnterprisePipelineStage(stage)) {
    return NextResponse.json({ error: "Invalid stage." }, { status: 400 });
  }
  if (status && !isEnterpriseLeadStatus(status)) {
    return NextResponse.json({ error: "Invalid status." }, { status: 400 });
  }
  if (priority && !isEnterprisePriority(priority)) {
    return NextResponse.json({ error: "Invalid priority." }, { status: 400 });
  }

  const tags =
    Array.isArray(body.tags)
      ? serializeTags(body.tags.map(String))
      : typeof body.tags === "string"
        ? body.tags
        : undefined;

  const estimatedValueUsd =
    body.estimatedValueUsd === null
      ? null
      : typeof body.estimatedValueUsd === "number"
        ? body.estimatedValueUsd
        : typeof body.estimatedValueUsd === "string" && body.estimatedValueUsd.trim()
          ? Number(body.estimatedValueUsd)
          : undefined;

  if (
    estimatedValueUsd !== undefined &&
    estimatedValueUsd !== null &&
    (!Number.isFinite(estimatedValueUsd) || estimatedValueUsd < 0)
  ) {
    return NextResponse.json(
      { error: "estimatedValueUsd must be a non-negative number or null." },
      { status: 400 }
    );
  }

  const result = await updateEnterpriseLead(id, {
    stage,
    status,
    priority,
    owner: body.owner === null ? null : typeof body.owner === "string" ? body.owner : undefined,
    notes: body.notes === null ? null : typeof body.notes === "string" ? body.notes : undefined,
    tags,
    estimatedValueUsd,
    lossReason:
      body.lossReason === null
        ? null
        : typeof body.lossReason === "string"
          ? body.lossReason
          : undefined,
    forecastCloseAt:
      body.forecastCloseAt === null
        ? null
        : typeof body.forecastCloseAt === "string"
          ? body.forecastCloseAt
          : undefined,
    actor: typeof body.actor === "string" ? body.actor : "admin",
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 404 });
  }
  return NextResponse.json({ ok: true, lead: result.lead });
}
