import { GlassSkeletonPanel, SkeletonBar } from "./ShimmerSkeleton";

export function ProfileSkeleton() {
  return (
    <div className="rtas-profile-wrap profile-page video-content-panel">
      <SkeletonBar className="mb-6 h-4 w-32" />
      <SkeletonBar className="mb-2 h-9 w-48" />
      <SkeletonBar className="mb-6 h-5 w-36" />

      <div className="grid gap-3">
        <GlassSkeletonPanel ariaLabel="Loading account details">
          <div className="flex flex-col gap-3">
            <SkeletonBar className="h-4 w-full" />
            <SkeletonBar className="h-4 w-4/5" />
            <SkeletonBar className="h-4 w-1/2" />
          </div>
        </GlassSkeletonPanel>

        <GlassSkeletonPanel ariaLabel="Loading subscription and credits">
          <div className="flex flex-col gap-3">
            <SkeletonBar className="h-4 w-full" />
            <SkeletonBar className="h-4 w-3/4" />
            <SkeletonBar className="h-4 w-2/3" />
            <SkeletonBar className="h-4 w-1/3" />
          </div>
        </GlassSkeletonPanel>
      </div>

      <div className="mt-6 flex flex-col gap-3">
        <SkeletonBar className="h-11 w-full rounded-lg" />
        <SkeletonBar className="h-11 w-full rounded-lg" />
        <SkeletonBar className="h-11 w-full rounded-lg" />
      </div>

      <div className="mt-8 flex gap-6">
        <SkeletonBar className="h-4 w-16" />
        <SkeletonBar className="h-4 w-16" />
        <SkeletonBar className="h-4 w-16" />
        <SkeletonBar className="h-4 w-16" />
      </div>
    </div>
  );
}
