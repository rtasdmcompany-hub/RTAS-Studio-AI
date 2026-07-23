/**
 * Support ticket helpers — real DB rows only; never seed fake tickets.
 */

import { randomBytes } from "crypto";
import { isPrismaConfigured, prisma } from "@/lib/prisma";

export const TICKET_CATEGORIES = [
  "account",
  "billing",
  "credits",
  "video_generation",
  "templates",
  "ai_models",
  "enterprise",
  "api",
  "security",
  "technical",
  "other",
] as const;

export type TicketCategory = (typeof TICKET_CATEGORIES)[number];

export const TICKET_PRIORITIES = ["low", "medium", "high", "urgent"] as const;
export type TicketPriority = (typeof TICKET_PRIORITIES)[number];

export const TICKET_STATUSES = [
  "open",
  "in_progress",
  "waiting_on_customer",
  "resolved",
  "closed",
] as const;
export type TicketStatus = (typeof TICKET_STATUSES)[number];

export type AttachmentInput = {
  fileName: string;
  contentType?: string;
  sizeBytes?: number;
  storageKey?: string;
};

export function isTicketCategory(value: string): value is TicketCategory {
  return (TICKET_CATEGORIES as readonly string[]).includes(value);
}

export function isTicketPriority(value: string): value is TicketPriority {
  return (TICKET_PRIORITIES as readonly string[]).includes(value);
}

export function isTicketStatus(value: string): value is TicketStatus {
  return (TICKET_STATUSES as readonly string[]).includes(value);
}

function makeTicketNumber(): string {
  const day = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const suffix = randomBytes(2).toString("hex").toUpperCase();
  return `RSAI-T-${day}-${suffix}`;
}

export async function createSupportTicket(input: {
  userId: string;
  category: TicketCategory;
  priority: TicketPriority;
  subject: string;
  description: string;
  attachments?: AttachmentInput[];
}) {
  if (!isPrismaConfigured()) {
    throw new Error("Database is not configured.");
  }

  const ticketNumber = makeTicketNumber();
  const attachments = (input.attachments ?? [])
    .filter((a) => a.fileName.trim())
    .slice(0, 5)
    .map((a) => ({
      fileName: a.fileName.trim().slice(0, 200),
      contentType: (a.contentType ?? "application/octet-stream").slice(0, 120),
      sizeBytes: Math.max(0, Math.min(a.sizeBytes ?? 0, 25 * 1024 * 1024)),
      storageKey: a.storageKey?.trim().slice(0, 500) || null,
    }));

  return prisma.supportTicket.create({
    data: {
      ticketNumber,
      userId: input.userId,
      category: input.category,
      priority: input.priority,
      subject: input.subject.trim().slice(0, 200),
      description: input.description.trim().slice(0, 8000),
      status: "open",
      attachments: attachments.length
        ? { create: attachments }
        : undefined,
    },
    include: {
      attachments: true,
      replies: { orderBy: { createdAt: "asc" } },
    },
  });
}

export async function listUserTickets(userId: string) {
  if (!isPrismaConfigured()) return [];
  return prisma.supportTicket.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    take: 100,
    include: {
      _count: { select: { replies: true, attachments: true } },
    },
  });
}

export async function getUserTicket(userId: string, ticketId: string) {
  if (!isPrismaConfigured()) return null;
  return prisma.supportTicket.findFirst({
    where: { id: ticketId, userId },
    include: {
      attachments: true,
      replies: {
        where: { isInternal: false },
        orderBy: { createdAt: "asc" },
      },
    },
  });
}

export async function addCustomerReply(input: {
  userId: string;
  ticketId: string;
  body: string;
}) {
  if (!isPrismaConfigured()) {
    throw new Error("Database is not configured.");
  }
  const ticket = await prisma.supportTicket.findFirst({
    where: { id: input.ticketId, userId: input.userId },
  });
  if (!ticket) return null;
  if (ticket.status === "closed") {
    throw new Error("Ticket is closed.");
  }

  const [reply] = await prisma.$transaction([
    prisma.supportTicketReply.create({
      data: {
        ticketId: ticket.id,
        authorRole: "customer",
        authorUserId: input.userId,
        body: input.body.trim().slice(0, 8000),
        isInternal: false,
      },
    }),
    prisma.supportTicket.update({
      where: { id: ticket.id },
      data: {
        status:
          ticket.status === "waiting_on_customer" || ticket.status === "resolved"
            ? "open"
            : ticket.status,
        updatedAt: new Date(),
      },
    }),
  ]);
  return reply;
}

export function serializeTicketForCustomer(
  ticket: Awaited<ReturnType<typeof getUserTicket>>
) {
  if (!ticket) return null;
  return {
    id: ticket.id,
    ticketNumber: ticket.ticketNumber,
    category: ticket.category,
    priority: ticket.priority,
    subject: ticket.subject,
    description: ticket.description,
    status: ticket.status,
    createdAt: ticket.createdAt.toISOString(),
    updatedAt: ticket.updatedAt.toISOString(),
    resolvedAt: ticket.resolvedAt?.toISOString() ?? null,
    closedAt: ticket.closedAt?.toISOString() ?? null,
    attachments: ticket.attachments.map((a) => ({
      id: a.id,
      fileName: a.fileName,
      contentType: a.contentType,
      sizeBytes: a.sizeBytes,
      storageKey: a.storageKey,
      createdAt: a.createdAt.toISOString(),
    })),
    replies: ticket.replies.map((r) => ({
      id: r.id,
      authorRole: r.authorRole,
      body: r.body,
      createdAt: r.createdAt.toISOString(),
    })),
  };
}
