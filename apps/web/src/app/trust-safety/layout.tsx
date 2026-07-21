import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trust & Safety",
  robots: { index: true, follow: true },
};

export default function TrustSafetyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
