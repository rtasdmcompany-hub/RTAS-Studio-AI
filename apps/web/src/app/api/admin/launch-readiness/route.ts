import { NextResponse } from "next/server";
import { buildLaunchReadinessPayload } from "@/lib/launch/readiness";
import { checklistProgress, LAUNCH_CHECKLIST, LAUNCH_MILESTONES } from "@/lib/launch/checklist";
import { isAdminAuthorized, adminUnauthorizedResponse } from "@/lib/server/api-auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const readiness = buildLaunchReadinessPayload();
  const progress = checklistProgress(LAUNCH_CHECKLIST);

  return NextResponse.json({
    ok: true,
    readiness,
    progress,
    milestones: LAUNCH_MILESTONES,
    checklist: LAUNCH_CHECKLIST,
  });
}
