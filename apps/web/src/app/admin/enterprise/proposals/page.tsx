import type { Metadata } from "next";
import { Suspense } from "react";
import { ProposalGeneratorClient } from "@/components/admin/ProposalGeneratorClient";
import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Enterprise Proposals",
  description: "Generate export-ready enterprise proposals for RTAS Studio AI.",
  path: "/admin/enterprise/proposals",
  noIndex: true,
});

export default function AdminEnterpriseProposalsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-ds-text-muted">Loading proposal generator…</div>}>
      <ProposalGeneratorClient />
    </Suspense>
  );
}
