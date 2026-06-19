import type { Metadata } from "next";
import "./globals.css";
import { PRODUCT_NAME } from "@rtas/shared";
import { AppProviders } from "@/components/providers/AppProviders";
import { GlobalShowcaseVideoBackground } from "@/components/marketing/GlobalShowcaseVideoBackground";
import { BRAND_FAVICON_PATH } from "@/lib/brand-assets";

export const metadata: Metadata = {
  title: `${PRODUCT_NAME} — Cinematic AI Video Studio`,
  description:
    "RTAS STUDIO AI is the creative suite to generate cinematic content, lock real faces, and finish scroll-stopping videos — all in one maintained studio.",
  icons: {
    icon: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
    shortcut: [BRAND_FAVICON_PATH],
    apple: [{ url: BRAND_FAVICON_PATH, type: "image/png" }],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <GlobalShowcaseVideoBackground />
          <div className="app-shell__content">
            <AppProviders>{children}</AppProviders>
          </div>
        </div>
      </body>
    </html>
  );
}
