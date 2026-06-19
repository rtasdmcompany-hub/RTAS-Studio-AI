import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";

export const metadata: Metadata = {
  title: `Terms of Service — ${PRODUCT_NAME}`,
  description:
    "Terms of Service, commercial rights, and copyright for RTAS Studio AI.",
};

export default function TermsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
