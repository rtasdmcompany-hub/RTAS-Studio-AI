import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: "System status",
  description: `Live health and readiness links for ${PRODUCT_NAME}.`,
};

const CHECKS = [
  {
    title: "Health",
    body: "Lightweight liveness probe used by hosting and uptime monitors.",
    href: "/api/health",
  },
  {
    title: "Readiness",
    body: "Dependency-aware readiness check for deploy and ops gates.",
    href: "/api/ready",
  },
] as const;

export default function StatusPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Status</p>
          <h1 className="text-white">System status</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Operational endpoints for {PRODUCT_NAME}. Open a check to see the live JSON response
            from this deployment.
          </p>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-2" aria-label="Status checks">
          {CHECKS.map((item) => (
            <InnerPageSection key={item.title} className="text-center">
              <h2 className="text-lg text-white">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                <ButtonLink href={item.href} variant="lavender">
                  Open {item.title.toLowerCase()}
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <InnerPageSection className="text-center">
          <p className="text-sm text-ds-text-muted">
            Account or billing issues? Visit Help Center — status pages are for service health only.
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
            <ButtonLink href="/developers" variant="ghost">
              Developers
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
