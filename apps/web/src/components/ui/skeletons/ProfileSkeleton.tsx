import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { GlassSkeletonPanel, SkeletonBar } from "@rtas/ui/skeletons";

/** Dashboard (/profile) skeleton — hero, status cards, actions, lists. */
export function ProfileSkeleton() {
  return (
    <MarketingLayout>
      <div
        className="rtas-profile-wrap profile-page profile-page--dashboard video-content-panel"
        aria-busy="true"
        role="status"
        aria-label="Loading dashboard"
      >
        <SkeletonBar className="mb-4 h-4 w-28" />

        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-col gap-2">
            <SkeletonBar className="h-3 w-20" />
            <SkeletonBar className="h-9 w-56" />
            <SkeletonBar className="h-4 w-72 max-w-full" />
          </div>
          <SkeletonBar className="h-11 w-44 rounded-lg" />
        </div>

        <div className="mb-6 grid gap-3 sm:grid-cols-3">
          <GlassSkeletonPanel ariaLabel="Loading credits">
            <div className="flex flex-col gap-3">
              <SkeletonBar className="h-3 w-16" />
              <SkeletonBar className="h-8 w-24" />
              <SkeletonBar className="h-3 w-32" />
            </div>
          </GlassSkeletonPanel>
          <GlassSkeletonPanel ariaLabel="Loading generation status">
            <div className="flex flex-col gap-3">
              <SkeletonBar className="h-3 w-24" />
              <SkeletonBar className="h-6 w-20" />
              <SkeletonBar className="h-2 w-full" />
            </div>
          </GlassSkeletonPanel>
          <GlassSkeletonPanel ariaLabel="Loading notifications">
            <div className="flex flex-col gap-3">
              <SkeletonBar className="h-3 w-24" />
              <SkeletonBar className="h-3 w-full" />
              <SkeletonBar className="h-3 w-4/5" />
            </div>
          </GlassSkeletonPanel>
        </div>

        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SkeletonBar className="h-20 w-full rounded-xl" />
          <SkeletonBar className="h-20 w-full rounded-xl" />
          <SkeletonBar className="h-20 w-full rounded-xl" />
          <SkeletonBar className="h-20 w-full rounded-xl" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <GlassSkeletonPanel ariaLabel="Loading recent projects">
            <div className="flex flex-col gap-3">
              <SkeletonBar className="h-12 w-full rounded-lg" />
              <SkeletonBar className="h-12 w-full rounded-lg" />
              <SkeletonBar className="h-12 w-full rounded-lg" />
            </div>
          </GlassSkeletonPanel>
          <GlassSkeletonPanel ariaLabel="Loading activity">
            <div className="flex flex-col gap-3">
              <SkeletonBar className="h-10 w-full" />
              <SkeletonBar className="h-10 w-full" />
              <SkeletonBar className="h-10 w-full" />
            </div>
          </GlassSkeletonPanel>
        </div>
      </div>
    </MarketingLayout>
  );
}
