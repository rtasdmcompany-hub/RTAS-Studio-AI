import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { AuthFlowGuard } from "@/components/auth/AuthFlowGuard";
import { AuthSkeleton } from "@/components/ui/skeletons";

export default function LoginPage() {
  return (
    <Suspense fallback={<AuthSkeleton />}>
      <AuthFlowGuard mode="login">
        <AuthForm mode="login" />
      </AuthFlowGuard>
    </Suspense>
  );
}
