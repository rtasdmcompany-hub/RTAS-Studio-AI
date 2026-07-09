import { GlassSkeletonPanel, SkeletonBar } from "./ShimmerSkeleton";

/** Studio workspace skeleton — sidebar controls + preview canvas. */
export function StudioSkeleton() {
  return (
    <div
      className="shashka-studio shashka-studio--loading min-h-screen"
      aria-busy="true"
      role="status"
      aria-label="Loading studio"
    >
      <div className="flex min-h-screen flex-col gap-4 p-4 lg:flex-row">
        <GlassSkeletonPanel className="w-full lg:w-96" ariaLabel="Loading studio controls">
          <SkeletonBar className="mb-4 h-5 w-40" />
          <div className="flex flex-col gap-3">
            <SkeletonBar className="h-10 w-full" />
            <SkeletonBar className="h-10 w-full" />
            <SkeletonBar className="h-24 w-full rounded-xl" />
            <SkeletonBar className="h-10 w-full" />
            <SkeletonBar className="h-10 w-full" />
            <SkeletonBar className="h-10 w-2/3" />
          </div>
        </GlassSkeletonPanel>

        <GlassSkeletonPanel className="flex-1" ariaLabel="Loading preview canvas">
          <SkeletonBar className="mb-4 h-5 w-32" />
          <SkeletonBar className="aspect-video w-full rounded-xl" />
          <div className="mt-4 flex flex-wrap gap-2">
            <SkeletonBar className="h-9 w-24" />
            <SkeletonBar className="h-9 w-24" />
            <SkeletonBar className="h-9 w-24" />
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <SkeletonBar className="h-16 w-full rounded-xl" />
            <SkeletonBar className="h-16 w-full rounded-xl" />
          </div>
        </GlassSkeletonPanel>
      </div>
    </div>
  );
}
