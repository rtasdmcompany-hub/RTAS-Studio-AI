import Link from "next/link";
import {
  COMPANY_NAME,
  GROUP_NAME,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LAST_UPDATED,
  PRODUCT_NAME,
} from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { BrandLockup } from "@/components/BrandLockup";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

type Props = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

export function LegalLayout({ title, subtitle, children }: Props) {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <div className="legal-shell legal-shell--marketing inner-page-legal">
          <InnerPageSection as="header" className="legal-header">
            <Link href="/" className="legal-home-link">
              ← Back to {PRODUCT_NAME}
            </Link>
            <div className="legal-brand">
              <BrandLockup logoVariant="icon" logoSize={64} />
              <h1 className="text-white">{title}</h1>
              {subtitle && <p className="legal-subtitle">{subtitle}</p>}
            </div>
            <p className="legal-meta">
              {LEGAL_ENTITY_STATEMENT}
              <br />
              {PRODUCT_NAME} · {COMPANY_NAME} · {GROUP_NAME}
              <br />
              Last updated: {LEGAL_LAST_UPDATED}
            </p>
          </InnerPageSection>

          <InnerPageSection className="legal-content !p-4 md:!p-6">{children}</InnerPageSection>

          <InnerPageSection as="nav" className="legal-nav legal-nav--inline" aria-label="Legal">
            <Link href="/terms">Terms of Service</Link>
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/refund">Refund Policy</Link>
            <Link href="/cookies">Cookies</Link>
          </InnerPageSection>
        </div>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
