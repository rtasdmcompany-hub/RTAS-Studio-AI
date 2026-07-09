import dynamic from "next/dynamic";
import { SiteFooter } from "./SiteFooter";

const LiveChatWidget = dynamic(
  () => import("./LiveChatWidget").then((mod) => mod.LiveChatWidget),
  { ssr: false }
);

const BackToTop = dynamic(
  () => import("./BackToTop").then((mod) => mod.BackToTop),
  { ssr: false }
);

const CookieConsent = dynamic(
  () => import("./CookieConsent").then((mod) => mod.CookieConsent),
  { ssr: false }
);

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
