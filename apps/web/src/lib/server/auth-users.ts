import { promises as fs } from "fs";
import path from "path";
import { randomUUID } from "crypto";
import bcrypt from "bcryptjs";
import type { UserProfile } from "@rtas/shared";
import { getDefaultProfile } from "@/lib/store";
import { saveServerProfile, getServerProfile } from "@/lib/server/profile-store";

const DATA_DIR = path.join(process.cwd(), ".data");
const AUTH_USERS_FILE = path.join(DATA_DIR, "auth-users.json");
/** Lower rounds = faster signup on slow disks; still fine for dev/local auth. */
const BCRYPT_ROUNDS = 10;

type AuthUserMap = Record<string, AuthUserRecord>;

let authUsersCache: { map: AuthUserMap; mtimeMs: number } | null = null;

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

export function isEmailVerified(user: AuthUserRecord): boolean {
  if (user.emailVerified === true) return true;
  if (user.emailVerified === false) return false;
  if (user.provider === "google" && !user.passwordHash) return true;
  return true;
}

export async function markAuthUserEmailVerified(userId: string): Promise<void> {
  const map = await readAll();
  const user = map[userId];
  if (!user) return;

  map[userId] = {
    ...user,
    emailVerified: true,
    emailVerifiedAt: new Date().toISOString(),
  };
  await writeAll(map);
}

async function ensureDataDir() {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function readAll(): Promise<AuthUserMap> {
  try {
    const stat = await fs.stat(AUTH_USERS_FILE);
    if (authUsersCache && authUsersCache.mtimeMs === stat.mtimeMs) {
      return authUsersCache.map;
    }
    const raw = await fs.readFile(AUTH_USERS_FILE, "utf-8");
    const map = JSON.parse(raw) as AuthUserMap;
    authUsersCache = { map, mtimeMs: stat.mtimeMs };
    return map;
  } catch {
    return {};
  }
}

async function writeAll(map: AuthUserMap) {
  await ensureDataDir();
  await fs.writeFile(AUTH_USERS_FILE, JSON.stringify(map, null, 2), "utf-8");
  authUsersCache = null;
}

function findInMap(map: AuthUserMap, email: string): AuthUserRecord | null {
  const normalized = normalizeEmail(email);
  return (
    Object.values(map).find((u) => normalizeEmail(u.email) === normalized) ?? null
  );
}

function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

export async function findAuthUserByEmail(
  email: string
): Promise<AuthUserRecord | null> {
  const map = await readAll();
  return findInMap(map, email);
}

export async function findAuthUserById(
  id: string
): Promise<AuthUserRecord | null> {
  const map = await readAll();
  return map[id] ?? null;
}

async function ensureStudioProfile(user: AuthUserRecord): Promise<UserProfile> {
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

  const map = await readAll();
  const existing = findInMap(map, email);

  if (existing?.passwordHash) {
    return {
      ok: false,
      error:
        "An account with this email already exists. Sign in with your password or continue with Google.",
    };
  }

  const passwordHash = await bcrypt.hash(input.password, BCRYPT_ROUNDS);

  if (existing) {
    const linked: AuthUserRecord = {
      ...existing,
      name: input.name.trim() || existing.name,
      passwordHash,
      emailVerified: false,
    };
    map[existing.id] = linked;
    await writeAll(map);
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
  await writeAll(map);
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
  const map = await readAll();
  const byEmail = await findAuthUserByEmail(email);

  if (byEmail) {
    const updated: AuthUserRecord = {
      ...byEmail,
      name: input.name || byEmail.name,
      image: input.image ?? byEmail.image,
      provider: byEmail.provider === "credentials" ? byEmail.provider : "google",
      emailVerified: true,
      emailVerifiedAt: byEmail.emailVerifiedAt ?? new Date().toISOString(),
    };
    map[byEmail.id] = updated;
    await writeAll(map);
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
  await writeAll(map);
  await ensureStudioProfile(user);
  return user;
}
