import { PRODUCT_NAME } from "@rtas/shared";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: `${PRODUCT_NAME} Admin`,
  description: "Owner dashboard for RTAS Studio AI operations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
