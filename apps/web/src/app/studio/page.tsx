import dynamic from "next/dynamic";
import { StudioSkeleton } from "@/components/ui/skeletons";

const StudioShell = dynamic(
  () => import("@/components/StudioShell").then((mod) => mod.StudioShell),
  {
    ssr: false,
    loading: () => <StudioSkeleton />,
  }
);

export default function StudioPage() {
  return <StudioShell />;
}
