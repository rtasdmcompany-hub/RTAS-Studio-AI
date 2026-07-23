import type { Metadata } from "next";
import { TicketDetailClient } from "./TicketDetailClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Ticket detail",
  description: "Support ticket conversation.",
  path: "/tickets",
  noIndex: true,
});

export default async function TicketDetailPage({
  params,
}: {
  params: Promise<{ ticketId: string }>;
}) {
  const { ticketId } = await params;
  return <TicketDetailClient ticketId={ticketId} />;
}
