import { Suspense } from "react";
import { CheckEmailClient } from "@/components/auth/CheckEmailClient";

export default function CheckEmailPage() {
  return (
    <Suspense fallback={<p className="auth-loading">Loading…</p>}>
      <CheckEmailClient />
    </Suspense>
  );
}
