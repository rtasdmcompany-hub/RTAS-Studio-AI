import { NextResponse } from "next/server";
import {
  adminUnauthorizedResponse,
  isAdminAuthorized,
} from "@/lib/server/api-auth";
import { isPrismaConfigured, prisma } from "@/lib/prisma";
import {
  isTicketPriority,
  isTicketStatus,
} from "@/lib/customer-success/tickets";

export const runtime = "nodejs";

/** Admin list — empty until real customers open tickets. No seed data. */
export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();
  if (!isPrismaConfigured()) {
    return NextResponse.json({ error: "Database is not configured." }, { status: 503 });
  }

  const url = new URL(request.url);
  const status = url.searchParams.get("status") || undefined;
  const take = Math.min(
    100,
    Math.max(1, Number.parseInt(url.searchParams.get("limit") || "50", 10) || 50)
  );

  const tickets = await prisma.supportTicket.findMany({
    where: status ? { status } : undefined,
    orderBy: { createdAt: "desc" },
    take,
    include: {
      user: { select: { id: true, email: true, tier: true } },
      _count: { select: { replies: true, attachments: true } },
    },
  });

  return NextResponse.json({
    ok: true,
    tickets: tickets.map((t) => ({
      id: t.id,
      ticketNumber: t.ticketNumber,
      category: t.category,
      priority: t.priority,
      subject: t.subject,
      status: t.status,
      adminNotes: t.adminNotes,
      createdAt: t.createdAt.toISOString(),
      updatedAt: t.updatedAt.toISOString(),
      user: t.user,
      replyCount: t._count.replies,
      attachmentCount: t._count.attachments,
    })),
  });
}

export async function PATCH(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();
  if (!isPrismaConfigured()) {
    return NextResponse.json({ error: "Database is not configured." }, { status: 503 });
  }

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const ticketId = typeof body.ticketId === "string" ? body.ticketId : "";
  if (!ticketId) {
    return NextResponse.json({ error: "ticketId is required." }, { status: 400 });
  }

  const data: {
    status?: string;
    priority?: string;
    adminNotes?: string;
    resolvedAt?: Date | null;
    closedAt?: Date | null;
  } = {};

  if (typeof body.status === "string") {
    if (!isTicketStatus(body.status)) {
      return NextResponse.json({ error: "Invalid status." }, { status: 400 });
    }
    data.status = body.status;
    if (body.status === "resolved") data.resolvedAt = new Date();
    if (body.status === "closed") data.closedAt = new Date();
    if (body.status === "open" || body.status === "in_progress") {
      data.resolvedAt = null;
      data.closedAt = null;
    }
  }
  if (typeof body.priority === "string") {
    if (!isTicketPriority(body.priority)) {
      return NextResponse.json({ error: "Invalid priority." }, { status: 400 });
    }
    data.priority = body.priority;
  }
  if (typeof body.adminNotes === "string") {
    data.adminNotes = body.adminNotes.trim().slice(0, 8000);
  }

  const replyBody =
    typeof body.replyBody === "string" ? body.replyBody.trim().slice(0, 8000) : "";
  const replyInternal = body.replyInternal === true;

  const ticket = await prisma.supportTicket.findUnique({ where: { id: ticketId } });
  if (!ticket) {
    return NextResponse.json({ error: "Ticket not found." }, { status: 404 });
  }

  const updated = await prisma.$transaction(async (tx) => {
    if (replyBody) {
      await tx.supportTicketReply.create({
        data: {
          ticketId,
          authorRole: "admin",
          body: replyBody,
          isInternal: replyInternal,
        },
      });
    }
    return tx.supportTicket.update({
      where: { id: ticketId },
      data,
      include: {
        replies: { orderBy: { createdAt: "asc" } },
        attachments: true,
        user: { select: { id: true, email: true, tier: true } },
      },
    });
  });

  return NextResponse.json({
    ok: true,
    ticket: {
      id: updated.id,
      ticketNumber: updated.ticketNumber,
      category: updated.category,
      priority: updated.priority,
      subject: updated.subject,
      description: updated.description,
      status: updated.status,
      adminNotes: updated.adminNotes,
      createdAt: updated.createdAt.toISOString(),
      updatedAt: updated.updatedAt.toISOString(),
      resolvedAt: updated.resolvedAt?.toISOString() ?? null,
      closedAt: updated.closedAt?.toISOString() ?? null,
      user: updated.user,
      attachments: updated.attachments,
      replies: updated.replies,
    },
  });
}
