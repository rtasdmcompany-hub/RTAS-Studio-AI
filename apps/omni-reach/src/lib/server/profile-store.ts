import type { UserProfile } from "@rtas/shared";
import { getDefaultProfile } from "@/lib/store";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { migrateJsonStoresToPrismaIfNeeded } from "@/lib/server/prisma-migrate";
import {
  prismaUserToProfile,
  profileToPrismaData,
} from "@/lib/server/user-mappers";
import { readJsonDocument, writeJsonDocument } from "@/lib/server/persistent-store";

const STORE_NAME = "profiles";

type ProfileMap = Record<string, UserProfile>;

async function ensurePrismaReady() {
  if (!isPrismaConfigured()) return false;
  await migrateJsonStoresToPrismaIfNeeded();
  return true;
}

async function readAllJson(): Promise<ProfileMap> {
  return readJsonDocument<ProfileMap>(STORE_NAME, {});
}

async function writeAllJson(map: ProfileMap) {
  await writeJsonDocument(STORE_NAME, map);
}

export async function getServerProfile(userId: string): Promise<UserProfile> {
  if (await ensurePrismaReady()) {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (user) return prismaUserToProfile(user);
  }

  const map = await readAllJson();
  return map[userId] ?? { ...getDefaultProfile(), id: userId };
}

export async function getServerProfileByEmail(
  email: string
): Promise<UserProfile | null> {
  if (await ensurePrismaReady()) {
    const user = await prisma.user.findUnique({
      where: { email: email.trim().toLowerCase() },
    });
    return user ? prismaUserToProfile(user) : null;
  }

  const map = await readAllJson();
  const normalized = email.trim().toLowerCase();
  return (
    Object.values(map).find((p) => p.email.trim().toLowerCase() === normalized) ??
    null
  );
}

export async function saveServerProfile(profile: UserProfile): Promise<UserProfile> {
  const updated: UserProfile = {
    ...profile,
    updatedAt: new Date().toISOString(),
  };

  if (await ensurePrismaReady()) {
    const data = profileToPrismaData(updated);
    const user = await prisma.user.upsert({
      where: { id: profile.id },
      create: {
        id: profile.id,
        provider: "credentials",
        emailVerified: false,
        ...data,
        email: profile.email.trim().toLowerCase(),
      },
      update: data,
    });
    return prismaUserToProfile(user);
  }

  const map = await readAllJson();
  map[profile.id] = updated;
  await writeAllJson(map);
  return updated;
}

/** Active paid customers for Fal pool sizing */
export async function listActivePaidProfiles(): Promise<UserProfile[]> {
  if (await ensurePrismaReady()) {
    const users = await prisma.user.findMany({
      where: {
        tier: { in: ["premium", "standard", "tester"] },
      },
    });
    return users.map(prismaUserToProfile);
  }

  const map = await readAllJson();
  const now = new Date();
  return Object.values(map).filter((p) => {
    if (p.tier !== "premium" && p.tier !== "standard" && p.tier !== "tester") {
      return false;
    }
    if (p.credits <= 0) return false;
    if (p.creditsExpireAt && new Date(p.creditsExpireAt) <= now) return false;
    return true;
  });
}
