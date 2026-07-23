import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";
import {
  PUBLIC_ROADMAP,
  ROADMAP_STATUS_LABEL,
  roadmapByStatus,
} from "@/lib/launch/roadmap";
import type { RoadmapItem } from "@/lib/launch/types";

export const metadata: Metadata = buildPageMetadata({
  title: "Product Roadmap",
  description: `Public product roadmap for ${PRODUCT_NAME} — Completed, In Progress, Planned, and Under Review. View only; honest items from real product state.`,
  path: "/roadmap",
  openGraphTitle: `Roadmap · ${PRODUCT_NAME}`,
});

const SECTIONS: Array<RoadmapItem["status"]> = [
  "completed",
  "in_progress",
  "under_review",
  "planned",
];

export default function RoadmapPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Product</p>
          <h1 className="text-zinc-100">Public roadmap</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            View-only roadmap for {PRODUCT_NAME}. Items reflect shipped and planned work —
            not fabricated ship guarantees or invented customer demand.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/feedback" variant="lavender">
              Request a feature
            </ButtonLink>
            <ButtonLink href="/help/changelog" variant="ghost">
              Release notes
            </ButtonLink>
            <ButtonLink href="/launch" variant="ghost">
              Launch Center
            </ButtonLink>
          </div>
        </InnerPageSection>

        <p className="text-center text-sm text-ds-text-muted">
          {PUBLIC_ROADMAP.length} items · updated with Phase 13 Sprint 9 GTM system
        </p>

        {SECTIONS.map((status) => {
          const items = roadmapByStatus(status);
          if (items.length === 0) return null;
          return (
            <InnerPageSection key={status}>
              <h2 className="text-xl text-zinc-100">{ROADMAP_STATUS_LABEL[status]}</h2>
              <ul className="mt-6 space-y-4">
                {items.map((item) => (
                  <li key={item.id} className="border-b border-white/10 pb-4">
                    <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                      {item.area}
                    </p>
                    <h3 className="mt-1 text-lg text-zinc-100">{item.title}</h3>
                    <p className="mt-1 text-sm text-ds-text-muted">{item.summary}</p>
                  </li>
                ))}
              </ul>
            </InnerPageSection>
          );
        })}
      </InnerPageContainer>
    </MarketingLayout>
  );
}
