import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/components/providers/AppProviders";
import { OmniReachDashboard } from "@/components/OmniReachDashboard";

export const metadata: Metadata = {
  title: "RTAS Omni Reach AI — Multi-Platform Publishing",
  description:
    "Connect social channels and publish or schedule ready-made content across every platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
