import { prisma, isPrismaConfigured } from "@/lib/prisma";

export const SOCIAL_PLATFORMS = [
  "YOUTUBE",
  "INSTAGRAM",
  "FACEBOOK",
  "TIKTOK",
  "X",
  "LINKEDIN",
] as const;

export type SocialPlatform = (typeof SOCIAL_PLATFORMS)[number];

export type SocialChannelStatus = {
  platform: SocialPlatform;
  connected: boolean;
  expiresAt: string | null;
  updatedAt: string | null;
};

export class DuplicatePlatformBindingError extends Error {
  constructor(platform: SocialPlatform) {
    super(
      `Only one active account can be connected for platform ${platform}. Disconnect or replace the existing channel before binding another one.`
    );
    this.name = "DuplicatePlatformBindingError";
  }
}

export class SocialRegistryNotConfiguredError extends Error {
  constructor() {
    super("Social registry requires Prisma and DATABASE_URL to be configured.");
    this.name = "SocialRegistryNotConfiguredError";
  }
}

export function normalizeSocialPlatform(platform: string): SocialPlatform {
  const normalized = platform.trim().toUpperCase();
  if (SOCIAL_PLATFORMS.includes(normalized as SocialPlatform)) {
    return normalized as SocialPlatform;
  }
  throw new Error(`Unsupported social platform: ${platform}`);
}

export async function getConnectedSocialChannels(
  userId: string
): Promise<SocialChannelStatus[]> {
  if (!isPrismaConfigured()) {
    throw new SocialRegistryNotConfiguredError();
  }

  const tokens = await prisma.socialToken.findMany({
    where: { userId },
    select: {
      platform: true,
      expiresAt: true,
      updatedAt: true,
    },
  });

  const tokenMap = new Map(
    tokens.map((token) => [
      normalizeSocialPlatform(token.platform),
      token,
    ])
  );

  return SOCIAL_PLATFORMS.map((platform) => {
    const token = tokenMap.get(platform);
    return {
      platform,
      connected: Boolean(token),
      expiresAt: token?.expiresAt?.toISOString() ?? null,
      updatedAt: token?.updatedAt?.toISOString() ?? null,
    };
  });
}

export async function bindSocialToken(input: {
  userId: string;
  platform: string;
  accessToken: string;
  refreshToken?: string | null;
  expiresAt?: string | Date | null;
  allowReplace?: boolean;
}) {
  if (!isPrismaConfigured()) {
    throw new SocialRegistryNotConfiguredError();
  }

  const platform = normalizeSocialPlatform(input.platform);
  const existing = await prisma.socialToken.findUnique({
    where: {
      userId_platform: {
        userId: input.userId,
        platform,
      },
    },
  });

  if (existing && !input.allowReplace) {
    throw new DuplicatePlatformBindingError(platform);
  }

  const expiresAt =
    input.expiresAt == null
      ? null
      : input.expiresAt instanceof Date
        ? input.expiresAt
        : new Date(input.expiresAt);

  return prisma.socialToken.upsert({
    where: {
      userId_platform: {
        userId: input.userId,
        platform,
      },
    },
    create: {
      userId: input.userId,
      platform,
      accessToken: input.accessToken,
      refreshToken: input.refreshToken ?? null,
      expiresAt,
    },
    update: {
      accessToken: input.accessToken,
      refreshToken: input.refreshToken ?? null,
      expiresAt,
    },
  });
}

export async function disconnectSocialToken(input: {
  userId: string;
  platform: string;
}) {
  if (!isPrismaConfigured()) {
    throw new SocialRegistryNotConfiguredError();
  }

  const platform = normalizeSocialPlatform(input.platform);

  await prisma.socialToken.deleteMany({
    where: {
      userId: input.userId,
      platform,
    },
  });

  return { platform, disconnected: true };
}
