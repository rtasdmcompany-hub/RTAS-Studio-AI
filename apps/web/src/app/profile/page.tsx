import { applyCreditExpiry } from "@/lib/store";
import { requireSession } from "@/lib/auth/require-session";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";
import dynamic from "next/dynamic";

const ProfileClient = dynamic(
  () =>
    import("@/components/profile/ProfileClient").then((mod) => mod.ProfileClient),
  {
    loading: () => (
      <div className="rtas-ui-loading-overlay" role="status" aria-live="polite">
        Loading dashboard…
      </div>
    ),
  }
);

export default async function ProfilePage() {
  const session = await requireSession("/profile");

  let profile = await getServerProfile(session.user.id);
  profile = {
    ...profile,
    id: session.user.id,
    email: session.user.email ?? profile.email,
    name: session.user.name ?? profile.name,
  };

  const expired = applyCreditExpiry(profile);
  if (expired.credits !== profile.credits) {
    profile = await saveServerProfile(expired);
  } else {
    profile = expired;
  }

  return <ProfileClient initialProfile={profile} />;
}
