import { PrismaClient } from "@/generated/prisma";

const globalForPrisma = globalThis as unknown as {
  omniReachPrisma: PrismaClient | undefined;
};

function createPrismaClient(): PrismaClient {
  return new PrismaClient({
    log:
      process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  });
}

export const prisma = globalForPrisma.omniReachPrisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.omniReachPrisma = prisma;
}

/** True when DATABASE_URL is set to a non-empty PostgreSQL connection string. */
export function isPrismaConfigured(): boolean {
  const url = process.env.DATABASE_URL?.trim() ?? "";
  return url.length > 0 && !url.includes("YOUR_PASSWORD");
}
