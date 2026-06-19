import { promises as fs } from "fs";
import path from "path";
import type { UserProfile } from "@rtas/shared";
import { getDefaultProfile } from "@/lib/store";

const DATA_DIR = path.join(process.cwd(), ".data");
const PROFILES_FILE = path.join(DATA_DIR, "profiles.json");

type ProfileMap = Record<string, UserProfile>;

async function ensureDataDir() {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function readAll(): Promise<ProfileMap> {
  try {
    const raw = await fs.readFile(PROFILES_FILE, "utf-8");
    return JSON.parse(raw) as ProfileMap;
  } catch {
    return {};
  }
}

async function writeAll(map: ProfileMap) {
  await ensureDataDir();
  await fs.writeFile(PROFILES_FILE, JSON.stringify(map, null, 2), "utf-8");
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
