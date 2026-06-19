import type { ReactNode } from "react";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <MarketingLayout>
      <div className="auth-shell">{children}</div>
    </MarketingLayout>
  );
}
