import Link from "next/link";
import {
  COMPANY_NAME,
  GROUP_NAME,
  LEGAL_LAST_UPDATED,
  PRODUCT_NAME,
} from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { BrandLockup } from "@/components/BrandLockup";

type Props = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

export function LegalLayout({ title, subtitle, children }: Props) {
  return (
    <MarketingLayout>
      <div className="legal-shell legal-shell--marketing">
        <header className="legal-header">
          <Link href="/" className="legal-home-link">
            ← Back to {PRODUCT_NAME}
          </Link>
          <div className="legal-brand">
            <BrandLockup logoVariant="icon" logoSize={64} />
            <h1>{title}</h1>
            {subtitle && <p className="legal-subtitle">{subtitle}</p>}
          </div>
          <p className="legal-meta">
            {PRODUCT_NAME} · {COMPANY_NAME} · {GROUP_NAME}
            <br />
            Last updated: {LEGAL_LAST_UPDATED}
          </p>
        </header>
        <div className="legal-content">{children}</div>
        <nav className="legal-nav legal-nav--inline">
          <Link href="/terms">Terms</Link>
          <Link href="/privacy">Privacy</Link>
          <Link href="/cookies">Cookies</Link>
        </nav>
      </div>
    </MarketingLayout>
  );
}
