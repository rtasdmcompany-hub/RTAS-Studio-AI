import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";

export const metadata: Metadata = {
  title: `Privacy Policy — ${PRODUCT_NAME}`,
};

export default function PrivacyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
