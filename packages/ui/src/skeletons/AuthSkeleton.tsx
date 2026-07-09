import { GlassSkeletonPanel, SkeletonBar } from "./ShimmerSkeleton";

export function AuthSkeleton() {
  return (
    <div className="auth-shell">
      <GlassSkeletonPanel
        className="mx-auto w-full max-w-[420px]"
        ariaLabel="Loading sign-in form"
      >
        <div className="flex flex-col items-center gap-4">
          <SkeletonBar className="h-12 w-12 rounded-full" />
          <SkeletonBar className="h-7 w-48" />
          <SkeletonBar className="h-4 w-64 max-w-full" />
        </div>

        <div className="mt-8 flex flex-col gap-4">
          <SkeletonBar className="h-11 w-full" />
          <SkeletonBar className="h-11 w-full" />
          <SkeletonBar className="h-11 w-full" />
        </div>

        <div className="mt-6 flex flex-col gap-3">
          <SkeletonBar className="h-10 w-full" />
          <SkeletonBar className="mx-auto h-4 w-40" />
        </div>
      </GlassSkeletonPanel>
    </div>
  );
}

export function AuthLinkSkeleton() {
  return (
    <GlassSkeletonPanel className="w-full" ariaLabel="Preparing confirmation link">
      <div className="flex flex-col gap-3">
        <SkeletonBar className="h-4 w-3/4" />
        <SkeletonBar className="h-11 w-full" />
      </div>
    </GlassSkeletonPanel>
  );
}
