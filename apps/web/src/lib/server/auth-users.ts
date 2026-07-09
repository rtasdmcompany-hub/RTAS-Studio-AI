import { randomUUID } from "crypto";
import bcrypt from "bcryptjs";
import type { UserProfile } from "@rtas/shared";
import { getDefaultProfile } from "@/lib/store";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { migrateJsonStoresToPrismaIfNeeded } from "@/lib/server/prisma-migrate";
import {
  prismaUserToAuthRecord,
  prismaUserToProfile,
  profileToPrismaData,
} from "@/lib/server/user-mappers";
import { readJsonDocument, writeJsonDocument } from "@/lib/server/persistent-store";
import {
  getServerProfile,
  saveServerProfile,
} from "@/lib/server/profile-store";

const STORE_NAME = "auth-users";
const BCRYPT_ROUNDS = 10;

type AuthUserMap = Record<string, AuthUserRecord>;

let authUsersCache: AuthUserMap | null = null;

export type AuthUserRecord = {
  id: string;
  email: string;
  name: string;
  passwordHash?: string;
  image?: string;
  provider: "credentials" | "google";
  emailVerified?: boolean;
  emailVerifiedAt?: string;
  createdAt: string;
};

function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

export function isEmailVerified(user: AuthUserRecord): boolean {
  if (user.emailVerified === true) return true;
  if (user.emailVerified === false) return false;
  if (user.provider === "google" && !user.passwordHash) return true;
  return true;
}

async function ensurePrismaReady() {
  if (!isPrismaConfigured()) return false;
  await migrateJsonStoresToPrismaIfNeeded();
  return true;
}

async function readAllJson(): Promise<AuthUserMap> {
  if (authUsersCache) return authUsersCache;
  const map = await readJsonDocument<AuthUserMap>(STORE_NAME, {});
  authUsersCache = map;
  return map;
}

async function writeAllJson(map: AuthUserMap) {
  await writeJsonDocument(STORE_NAME, map);
  authUsersCache = map;
}

function findInMap(map: AuthUserMap, email: string): AuthUserRecord | null {
  const normalized = normalizeEmail(email);
  return (
    Object.values(map).find((u) => normalizeEmail(u.email) === normalized) ?? null
  );
}

export async function markAuthUserEmailVerified(userId: string): Promise<void> {
  if (await ensurePrismaReady()) {
    await prisma.user.update({
      where: { id: userId },
      data: { emailVerified: true },
    });
    return;
  }

  const map = await readAllJson();
  const user = map[userId];
  if (!user) return;

  map[userId] = {
    ...user,
    emailVerified: true,
    emailVerifiedAt: new Date().toISOString(),
  };
  await writeAllJson(map);
}

export async function findAuthUserByEmail(
  email: string
): Promise<AuthUserRecord | null> {
  if (await ensurePrismaReady()) {
    const user = await prisma.user.findUnique({
      where: { email: normalizeEmail(email) },
    });
    return user ? prismaUserToAuthRecord(user) : null;
  }

  const map = await readAllJson();
  return findInMap(map, email);
}

export async function findAuthUserById(
  id: string
): Promise<AuthUserRecord | null> {
  if (await ensurePrismaReady()) {
    const user = await prisma.user.findUnique({ where: { id } });
    return user ? prismaUserToAuthRecord(user) : null;
  }

  const map = await readAllJson();
  return map[id] ?? null;
}

async function ensureStudioProfile(user: AuthUserRecord): Promise<UserProfile> {
  if (await ensurePrismaReady()) {
    const existing = await prisma.user.findUnique({ where: { id: user.id } });
    if (existing) {
      const profile = prismaUserToProfile(existing);
      if (profile.name !== user.name) {
        const updated = await prisma.user.update({
          where: { id: user.id },
          data: { name: user.name },
        });
        return prismaUserToProfile(updated);
      }
      return profile;
    }
  }

  const existing = await getServerProfile(user.id);
  if (existing.id === user.id && existing.email === user.email) {
    if (existing.name !== user.name) {
      return saveServerProfile({ ...existing, name: user.name });
    }
    return existing;
  }

  const profile: UserProfile = {
    ...getDefaultProfile(),
    id: user.id,
    email: user.email,
    name: user.name,
    createdAt: user.createdAt,
  };
  return saveServerProfile(profile);
}

export async function registerCredentialsUser(input: {
  email: string;
  password: string;
  name: string;
}): Promise<
  | {
      ok: true;
      userId: string;
      email: string;
      linkedGoogleAccount?: boolean;
      needsEmailVerification: boolean;
    }
  | { ok: false; error: string }
> {
  const email = normalizeEmail(input.email);
  if (!email.includes("@")) {
    return { ok: false, error: "Enter a valid email address." };
  }
  if (input.password.length < 8) {
    return { ok: false, error: "Password must be at least 8 characters." };
  }
  if (!input.name.trim()) {
    return { ok: false, error: "Name is required." };
  }

  const passwordHash = await bcrypt.hash(input.password, BCRYPT_ROUNDS);

  if (await ensurePrismaReady()) {
    const existing = await prisma.user.findUnique({ where: { email } });

    if (existing?.passwordHash) {
      return {
        ok: false,
        error:
          "An account with this email already exists. Sign in with your password or continue with Google.",
      };
    }

    if (existing) {
      const updated = await prisma.user.update({
        where: { id: existing.id },
        data: {
          name: input.name.trim() || existing.name,
          passwordHash,
          emailVerified: false,
          provider: "credentials",
        },
      });
      await ensureStudioProfile(prismaUserToAuthRecord(updated));
      return {
        ok: true,
        userId: updated.id,
        email: updated.email,
        linkedGoogleAccount: existing.provider === "google",
        needsEmailVerification: true,
      };
    }

    const created = await prisma.user.create({
      data: {
        email,
        name: input.name.trim(),
        passwordHash,
        provider: "credentials",
        emailVerified: false,
      },
    });
    await ensureStudioProfile(prismaUserToAuthRecord(created));
    return {
      ok: true,
      userId: created.id,
      email: created.email,
      needsEmailVerification: true,
    };
  }

  const map = await readAllJson();
  const existing = findInMap(map, email);

  if (existing?.passwordHash) {
    return {
      ok: false,
      error:
        "An account with this email already exists. Sign in with your password or continue with Google.",
    };
  }

  if (existing) {
    const linked: AuthUserRecord = {
      ...existing,
      name: input.name.trim() || existing.name,
      passwordHash,
      emailVerified: false,
    };
    map[existing.id] = linked;
    await writeAllJson(map);
    await ensureStudioProfile(linked);
    return {
      ok: true,
      userId: existing.id,
      email: linked.email,
      linkedGoogleAccount: true,
      needsEmailVerification: true,
    };
  }

  const id = randomUUID();
  const user: AuthUserRecord = {
    id,
    email,
    name: input.name.trim(),
    passwordHash,
    provider: "credentials",
    emailVerified: false,
    createdAt: new Date().toISOString(),
  };

  map[id] = user;
  await writeAllJson(map);
  await ensureStudioProfile(user);

  return {
    ok: true,
    userId: id,
    email: user.email,
    needsEmailVerification: true,
  };
}

export async function verifyCredentials(
  email: string,
  password: string
): Promise<AuthUserRecord | null> {
  const user = await findAuthUserByEmail(email);
  if (!user?.passwordHash) return null;
  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid || !isEmailVerified(user)) return null;
  return user;
}

export async function upsertOAuthUser(input: {
  id: string;
  email: string;
  name: string;
  image?: string | null;
}): Promise<AuthUserRecord> {
  const email = normalizeEmail(input.email);

  if (await ensurePrismaReady()) {
    const byEmail = await prisma.user.findUnique({ where: { email } });

    if (byEmail) {
      // Refuse to attach Google to a password account without explicit linking.
      if (byEmail.passwordHash && byEmail.provider === "credentials") {
        throw new Error(
          "OAuth account linking blocked: email already registered with a password."
        );
      }

      const updated = await prisma.user.update({
        where: { id: byEmail.id },
        data: {
          name: input.name || byEmail.name,
          image: input.image ?? byEmail.image,
          provider: "google",
          emailVerified: true,
        },
      });
      await ensureStudioProfile(prismaUserToAuthRecord(updated));
      return prismaUserToAuthRecord(updated);
    }

    const created = await prisma.user.upsert({
      where: { email },
      create: {
        id: input.id,
        email,
        name: input.name || email.split("@")[0],
        image: input.image ?? null,
        provider: "google",
        emailVerified: true,
        passwordHash: null,
      },
      update: {
        name: input.name || email.split("@")[0],
        image: input.image ?? null,
        emailVerified: true,
      },
    });
    await ensureStudioProfile(prismaUserToAuthRecord(created));
    return prismaUserToAuthRecord(created);
  }

  const map = await readAllJson();
  const byEmail = findInMap(map, email);

  if (byEmail) {
    if (byEmail.passwordHash && byEmail.provider === "credentials") {
      throw new Error(
        "OAuth account linking blocked: email already registered with a password."
      );
    }

    const updated: AuthUserRecord = {
      ...byEmail,
      name: input.name || byEmail.name,
      image: input.image ?? byEmail.image,
      provider: "google",
      emailVerified: true,
      emailVerifiedAt: byEmail.emailVerifiedAt ?? new Date().toISOString(),
    };
    map[byEmail.id] = updated;
    await writeAllJson(map);
    await ensureStudioProfile(updated);
    return updated;
  }

  const user: AuthUserRecord = {
    id: input.id,
    email,
    name: input.name || email.split("@")[0],
    image: input.image ?? undefined,
    provider: "google",
    emailVerified: true,
    emailVerifiedAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
  };
  map[user.id] = user;
  await writeAllJson(map);
  await ensureStudioProfile(user);
  return user;
}
