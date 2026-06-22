import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { AuthFlowGuard } from "@/components/auth/AuthFlowGuard";

export default function LoginPage() {
  return (
    <Suspense fallback={<p className="auth-loading">Loading…</p>}>
      <AuthFlowGuard mode="login">
        <AuthForm mode="login" />
      </AuthFlowGuard>
    </Suspense>
  );
}
