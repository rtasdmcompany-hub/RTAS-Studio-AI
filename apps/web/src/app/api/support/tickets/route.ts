import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import { isPrismaConfigured } from "@/lib/prisma";
import {
  createSupportTicket,
  isTicketCategory,
  isTicketPriority,
  listUserTickets,
  serializeTicketForCustomer,
  getUserTicket,
} from "@/lib/customer-success/tickets";

export const runtime = "nodejs";

function asTrimmed(value: unknown, max: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

export async function GET() {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;
  if (!isPrismaConfigured()) {
    return NextResponse.json(
      { error: "Database is not configured.", tickets: [] },
      { status: 503 }
    );
  }

  const rows = await listUserTickets(auth.userId);
  return NextResponse.json({
    ok: true,
    tickets: rows.map((t) => ({
      id: t.id,
      ticketNumber: t.ticketNumber,
      category: t.category,
      priority: t.priority,
      subject: t.subject,
      status: t.status,
      createdAt: t.createdAt.toISOString(),
      updatedAt: t.updatedAt.toISOString(),
      replyCount: t._count.replies,
      attachmentCount: t._count.attachments,
    })),
  });
}

export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `support-ticket:${auth.userId}:${ip}`,
    8,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  if (!isPrismaConfigured()) {
    return NextResponse.json(
      { error: "Database is not configured." },
      { status: 503 }
    );
  }

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const category = asTrimmed(body.category, 40).toLowerCase();
  const priority = asTrimmed(body.priority, 20).toLowerCase() || "medium";
  const subject = asTrimmed(body.subject, 200);
  const description = asTrimmed(body.description, 8000);

  if (!isTicketCategory(category)) {
    return NextResponse.json({ error: "Invalid category." }, { status: 400 });
  }
  if (!isTicketPriority(priority)) {
    return NextResponse.json({ error: "Invalid priority." }, { status: 400 });
  }
  if (subject.length < 4) {
    return NextResponse.json(
      { error: "Subject must be at least 4 characters." },
      { status: 400 }
    );
  }
  if (description.length < 10) {
    return NextResponse.json(
      { error: "Description must be at least 10 characters." },
      { status: 400 }
    );
  }

  const rawAttachments = Array.isArray(body.attachments) ? body.attachments : [];
  const attachments = rawAttachments
    .slice(0, 5)
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const row = item as Record<string, unknown>;
      const fileName = asTrimmed(row.fileName, 200);
      if (!fileName) return null;
      return {
        fileName,
        contentType: asTrimmed(row.contentType, 120) || "application/octet-stream",
        sizeBytes:
          typeof row.sizeBytes === "number"
            ? row.sizeBytes
            : Number.parseInt(String(row.sizeBytes ?? "0"), 10) || 0,
        storageKey: asTrimmed(row.storageKey, 500) || undefined,
      };
    })
    .filter(Boolean) as Array<{
    fileName: string;
    contentType: string;
    sizeBytes: number;
    storageKey?: string;
  }>;

  try {
    const ticket = await createSupportTicket({
      userId: auth.userId,
      category,
      priority,
      subject,
      description,
      attachments,
    });
    const full = await getUserTicket(auth.userId, ticket.id);
    return NextResponse.json(
      { ok: true, ticket: serializeTicketForCustomer(full) },
      { status: 201 }
    );
  } catch (err) {
    return NextResponse.json(
      {
        error: err instanceof Error ? err.message : "Could not create ticket.",
      },
      { status: 500 }
    );
  }
}
