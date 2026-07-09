import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { GlobalSiteHeader } from "@/components/layout/GlobalSiteHeader";
import { AppProviders } from "@/components/providers/AppProviders";
import { rootMetadata } from "@/lib/site-metadata";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = rootMetadata;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>
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
