import { LoadingOverlay } from "@rtas/ui";

export default function RouteLoading() {
  return (
    <div className="rtas-fullpage-state">
      <LoadingOverlay label="Loading…" />
    </div>
  );
}
