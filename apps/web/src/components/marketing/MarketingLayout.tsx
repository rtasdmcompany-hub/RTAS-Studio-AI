import { CookieConsent } from "./CookieConsent";
import { LiveChatWidget } from "./LiveChatWidget";
import { BackToTop } from "./BackToTop";
import { SiteFooter } from "./SiteFooter";

type Props = {
  children: React.ReactNode;
  /** Studio uses its own shell — marketing pages use full chrome. */
  showChrome?: boolean;
};

export function MarketingLayout({ children, showChrome = true }: Props) {
  if (!showChrome) return <>{children}</>;

  return (
    <div className="rtas-marketing-shell">
      <main className="rtas-marketing-main">{children}</main>
      <SiteFooter />
      <BackToTop />
      <LiveChatWidget />
      <CookieConsent />
    </div>
  );
}
