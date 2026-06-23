import type { User } from "@prisma/client";
import type { UserProfile } from "@rtas/shared";
import { getDefaultProfile } from "@/lib/store";
import type { AuthUserRecord } from "@/lib/server/auth-users";

export function prismaUserToAuthRecord(user: User): AuthUserRecord {
  return {
    id: user.id,
    email: user.email,
    name: user.name ?? user.email.split("@")[0],
    passwordHash: user.passwordHash ?? undefined,
    image: user.image ?? undefined,
    provider: user.provider === "google" ? "google" : "credentials",
    emailVerified: user.emailVerified,
    emailVerifiedAt: user.emailVerified ? user.updatedAt.toISOString() : undefined,
    createdAt: user.createdAt.toISOString(),
  };
}

export function prismaUserToProfile(user: User): UserProfile {
  const base = getDefaultProfile();
  return {
    ...base,
    id: user.id,
    email: user.email,
    name: user.name ?? base.name,
    tier: (user.tier as UserProfile["tier"]) ?? "free",
    subscriptionActive: user.tier === "tester",
    paymentProvider:
      (user.paymentProvider as UserProfile["paymentProvider"]) ?? undefined,
    externalCustomerId: user.externalCustomerId ?? undefined,
    externalSubscriptionId: user.externalSubscriptionId ?? undefined,
    createdAt: user.createdAt.toISOString(),
    updatedAt: user.updatedAt.toISOString(),
  };
}

export function profileToPrismaData(profile: UserProfile) {
  return {
    tier: profile.tier,
    paymentProvider: profile.paymentProvider ?? null,
    externalCustomerId: profile.externalCustomerId ?? null,
    externalSubscriptionId: profile.externalSubscriptionId ?? null,
    name: profile.name,
    email: profile.email,
  };
}
