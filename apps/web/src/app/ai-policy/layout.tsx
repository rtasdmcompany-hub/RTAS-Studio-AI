import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Usage Policy",
  robots: { index: true, follow: true },
};

export default function AiPolicyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
