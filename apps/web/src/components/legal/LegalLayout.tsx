import Link from "next/link";
import {
  COMPANY_NAME,
  LEGAL_DOCUMENT_VERSION,
  LEGAL_EFFECTIVE_DATE,
  LEGAL_ENTITY_STATEMENT,
  LEGAL_LAST_UPDATED,
  LEGAL_LOCATION_STATEMENT,
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
              {PRODUCT_NAME} · {COMPANY_NAME} · {LEGAL_LOCATION_STATEMENT}
              <br />
              Document Version {LEGAL_DOCUMENT_VERSION}
              <br />
              Effective Date: {LEGAL_EFFECTIVE_DATE}
              <br />
              Last Updated: {LEGAL_LAST_UPDATED}
            </p>
          </InnerPageSection>

          <InnerPageSection className="legal-content !p-4 md:!p-6">{children}</InnerPageSection>

          <InnerPageSection as="nav" className="legal-nav legal-nav--inline" aria-label="Legal">
            <Link href="/terms">Terms of Service</Link>
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/refund">Refund Policy</Link>
            <Link href="/cookies">Cookie Policy</Link>
            <Link href="/ai-policy">AI Usage Policy</Link>
            <Link href="/trust-safety">Trust &amp; Safety</Link>
          </InnerPageSection>
        </div>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
