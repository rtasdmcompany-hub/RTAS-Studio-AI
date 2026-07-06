import type { Metadata } from "next";
import "./globals.css";
import { GlobalSiteHeader } from "@/components/layout/GlobalSiteHeader";
import { AppProviders } from "@/components/providers/AppProviders";
import { rootMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = rootMetadata;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell cinematic-atmosphere">
          <div className="app-shell__content">
            <AppProviders>
              <GlobalSiteHeader />
              {children}
            </AppProviders>
          </div>
        </div>
      </body>
    </html>
  );
}
