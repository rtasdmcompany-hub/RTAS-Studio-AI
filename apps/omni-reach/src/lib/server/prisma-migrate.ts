import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { readJsonDocument } from "@/lib/server/persistent-store";
import { profileToPrismaData } from "@/lib/server/user-mappers";
import type { AuthUserRecord } from "@/lib/server/auth-users";
import type { UserProfile } from "@rtas/shared";

let migrationPromise: Promise<void> | null = null;

/**
 * One-time import of legacy auth-users + profiles JSON/Redis documents into Postgres.
 */
export async function migrateJsonStoresToPrismaIfNeeded(): Promise<void> {
  if (!isPrismaConfigured()) return;

  if (!migrationPromise) {
    migrationPromise = runMigration();
  }
  await migrationPromise;
}

async function runMigration(): Promise<void> {
  const existingCount = await prisma.user.count();
  if (existingCount > 0) return;

  const authMap = await readJsonDocument<Record<string, AuthUserRecord>>(
    "auth-users",
    {}
  );
  const profileMap = await readJsonDocument<Record<string, UserProfile>>(
    "profiles",
    {}
  );

  const authUsers = Object.values(authMap);
  if (authUsers.length === 0) return;

  for (const auth of authUsers) {
    const profile = profileMap[auth.id];
    const email = auth.email.trim().toLowerCase();

    await prisma.user.upsert({
      where: { email },
      create: {
        id: auth.id,
        email,
        name: auth.name,
        passwordHash: auth.passwordHash ?? null,
        image: auth.image ?? null,
        provider: auth.provider,
        emailVerified:
          auth.emailVerified === true ||
          (auth.provider === "google" && !auth.passwordHash),
        createdAt: new Date(auth.createdAt),
        ...(profile ? profileToPrismaData(profile) : {}),
      },
      update: {
        name: auth.name,
        passwordHash: auth.passwordHash ?? null,
        image: auth.image ?? null,
        provider: auth.provider,
        emailVerified:
          auth.emailVerified === true ||
          (auth.provider === "google" && !auth.passwordHash),
        ...(profile ? profileToPrismaData(profile) : {}),
      },
    });
  }

  console.info(
    `[prisma] Migrated ${authUsers.length} user(s) from JSON/Redis into Postgres`
  );
}
