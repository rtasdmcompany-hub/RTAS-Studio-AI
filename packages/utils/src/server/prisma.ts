import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

function createPrismaClient(): PrismaClient {
  return new PrismaClient({
    log:
      process.env.NODE_ENV === "development"
        ? ["error", "warn"]
        : ["error"],
  });
}

export const prisma = globalForPrisma.prisma ?? createPrismaClient();

// Reuse the client across warm serverless isolates (dev HMR + production).
globalForPrisma.prisma = prisma;

/** True when DATABASE_URL is set to a non-empty PostgreSQL connection string. */
export function isPrismaConfigured(): boolean {
  const url = process.env.DATABASE_URL?.trim() ?? "";
  return url.length > 0 && !url.includes("YOUR_PASSWORD");
}
