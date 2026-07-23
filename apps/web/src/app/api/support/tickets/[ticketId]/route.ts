import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import { isPrismaConfigured } from "@/lib/prisma";
import {
  addCustomerReply,
  getUserTicket,
  serializeTicketForCustomer,
} from "@/lib/customer-success/tickets";

export const runtime = "nodejs";

type Ctx = { params: Promise<{ ticketId: string }> };

export async function GET(_request: Request, context: Ctx) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;
  if (!isPrismaConfigured()) {
    return NextResponse.json({ error: "Database is not configured." }, { status: 503 });
  }

  const { ticketId } = await context.params;
  const ticket = await getUserTicket(auth.userId, ticketId);
  if (!ticket) {
    return NextResponse.json({ error: "Ticket not found." }, { status: 404 });
  }
  return NextResponse.json({ ok: true, ticket: serializeTicketForCustomer(ticket) });
}

export async function POST(request: Request, context: Ctx) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(
    `support-reply:${auth.userId}:${ip}`,
    30,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  if (!isPrismaConfigured()) {
    return NextResponse.json({ error: "Database is not configured." }, { status: 503 });
  }

  const { ticketId } = await context.params;
  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const message =
    typeof body.body === "string"
      ? body.body.trim()
      : typeof body.message === "string"
        ? body.message.trim()
        : "";
  if (message.length < 2) {
    return NextResponse.json({ error: "Reply body is required." }, { status: 400 });
  }

  try {
    const reply = await addCustomerReply({
      userId: auth.userId,
      ticketId,
      body: message,
    });
    if (!reply) {
      return NextResponse.json({ error: "Ticket not found." }, { status: 404 });
    }
    const ticket = await getUserTicket(auth.userId, ticketId);
    return NextResponse.json({
      ok: true,
      reply: {
        id: reply.id,
        authorRole: reply.authorRole,
        body: reply.body,
        createdAt: reply.createdAt.toISOString(),
      },
      ticket: serializeTicketForCustomer(ticket),
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Could not add reply." },
      { status: 400 }
    );
  }
}
