import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { buildProposalMarkdown, nextProposalNumber } from "@/lib/enterprise/proposal";

export const runtime = "nodejs";

function asTrimmedString(value: unknown, max = 8000): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();
  if (!isPrismaConfigured()) {
    return NextResponse.json({ ok: true, proposals: [], dbConfigured: false });
  }

  const url = new URL(request.url);
  const id = url.searchParams.get("id");
  if (id) {
    const proposal = await prisma.enterpriseProposal.findUnique({ where: { id } });
    if (!proposal) {
      return NextResponse.json({ error: "Proposal not found." }, { status: 404 });
    }
    return NextResponse.json({ ok: true, proposal, dbConfigured: true });
  }

  const proposals = await prisma.enterpriseProposal.findMany({
    orderBy: { createdAt: "desc" },
    take: 50,
  });
  return NextResponse.json({ ok: true, proposals, dbConfigured: true });
}

export async function POST(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const customerName = asTrimmedString(body.customerName, 200);
  if (!customerName) {
    return NextResponse.json({ error: "Customer name is required." }, { status: 400 });
  }

  const customerContact = asTrimmedString(body.customerContact, 200) || undefined;
  const customerEmail = asTrimmedString(body.customerEmail, 254) || undefined;
  const requirements = asTrimmedString(body.requirements, 8000) || undefined;
  const solution = asTrimmedString(body.solution, 8000) || undefined;
  const timeline = asTrimmedString(body.timeline, 4000) || undefined;
  const pricingNotes = asTrimmedString(body.pricingNotes, 4000) || undefined;
  const supportNotes = asTrimmedString(body.supportNotes, 4000) || undefined;
  const acceptanceNotes = asTrimmedString(body.acceptanceNotes, 4000) || undefined;
  const leadId = asTrimmedString(body.leadId, 80) || undefined;
  const persist = body.persist !== false;

  let proposalNumber =
    asTrimmedString(body.proposalNumber, 40) ||
    nextProposalNumber(
      isPrismaConfigured() ? await prisma.enterpriseProposal.count() : 0
    );

  const markdownBody = buildProposalMarkdown({
    proposalNumber,
    customerName,
    customerContact,
    customerEmail,
    requirements,
    solution,
    timeline,
    pricingNotes,
    supportNotes,
    acceptanceNotes,
  });

  if (!persist || !isPrismaConfigured()) {
    return NextResponse.json({
      ok: true,
      persisted: false,
      proposal: {
        proposalNumber,
        customerName,
        customerContact,
        customerEmail,
        markdownBody,
        status: "draft",
      },
    });
  }

  // Ensure unique proposal number
  const existing = await prisma.enterpriseProposal.findUnique({
    where: { proposalNumber },
  });
  if (existing) {
    proposalNumber = nextProposalNumber(await prisma.enterpriseProposal.count());
  }

  const id = randomUUID();
  const proposal = await prisma.enterpriseProposal.create({
    data: {
      id,
      proposalNumber,
      leadId: leadId || null,
      customerName,
      customerContact: customerContact || null,
      customerEmail: customerEmail || null,
      requirements: requirements || null,
      solution: solution || null,
      timeline: timeline || null,
      pricingNotes: pricingNotes || null,
      supportNotes: supportNotes || null,
      acceptanceNotes: acceptanceNotes || null,
      markdownBody,
      status: "draft",
      createdBy: "admin",
    },
  });

  if (leadId) {
    await prisma.enterpriseLeadActivity.create({
      data: {
        id: randomUUID(),
        leadId,
        type: "proposal",
        body: `Proposal ${proposalNumber} generated.`,
        actor: "admin",
      },
    });
    await prisma.enterpriseLead.update({
      where: { id: leadId },
      data: { stage: "proposal_sent", status: "open" },
    });
  }

  return NextResponse.json({ ok: true, persisted: true, proposal });
}
