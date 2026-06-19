import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { AuthFlowGuard } from "@/components/auth/AuthFlowGuard";

export default function SignupPage() {
  return (
    <Suspense fallback={<p className="auth-loading">Loading…</p>}>
      <AuthFlowGuard mode="signup" />
      <AuthForm mode="signup" />
    </Suspense>
  );
}
