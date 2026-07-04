import { Suspense } from "react";
import { CheckEmailClient } from "@/components/auth/CheckEmailClient";
import { AuthSkeleton } from "@/components/ui/skeletons";

export default function CheckEmailPage() {
  return (
    <Suspense fallback={<AuthSkeleton />}>
      <CheckEmailClient />
    </Suspense>
  );
}
