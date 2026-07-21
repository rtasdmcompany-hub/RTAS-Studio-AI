import { Suspense } from "react";
import { ForgotPasswordClient } from "@/components/auth/ForgotPasswordClient";
import { AuthSkeleton } from "@/components/ui/skeletons";

export default function ForgotPasswordPage() {
  return (
    <Suspense fallback={<AuthSkeleton />}>
      <ForgotPasswordClient />
    </Suspense>
  );
}
