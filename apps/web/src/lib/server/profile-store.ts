import type { UserProfile } from "@rtas/shared";
import { getDefaultProfile } from "@/lib/store";
import { readJsonDocument, writeJsonDocument } from "@/lib/server/persistent-store";

const STORE_NAME = "profiles";

type ProfileMap = Record<string, UserProfile>;

async function readAll(): Promise<ProfileMap> {
  return readJsonDocument<ProfileMap>(STORE_NAME, {});
}

async function writeAll(map: ProfileMap) {
  await writeJsonDocument(STORE_NAME, map);
}

export async function getServerProfile(userId: string): Promise<UserProfile> {
  const map = await readAll();
  return map[userId] ?? { ...getDefaultProfile(), id: userId };
}

export async function getServerProfileByEmail(
  email: string
): Promise<UserProfile | null> {
  const map = await readAll();
  const normalized = email.trim().toLowerCase();
  return (
    Object.values(map).find((p) => p.email.trim().toLowerCase() === normalized) ??
    null
  );
}

export async function saveServerProfile(profile: UserProfile): Promise<UserProfile> {
  const map = await readAll();
  const updated: UserProfile = {
    ...profile,
    updatedAt: new Date().toISOString(),
  };
  map[profile.id] = updated;
  await writeAll(map);
  return updated;
}

/** Active paid customers for Fal pool sizing */
export async function listActivePaidProfiles(): Promise<UserProfile[]> {
  const map = await readAll();
  const now = new Date();
  return Object.values(map).filter((p) => {
    if (p.tier !== "premium" && p.tier !== "standard" && p.tier !== "tester") return false;
    if (p.credits <= 0) return false;
    if (p.creditsExpireAt && new Date(p.creditsExpireAt) <= now) return false;
    return true;
  });
}
