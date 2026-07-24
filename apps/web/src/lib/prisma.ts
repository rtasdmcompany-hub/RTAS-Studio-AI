// Import prisma only — avoid @rtas/utils/server barrel (pulls persistent-store → fs into client bundles).
export { prisma, isPrismaConfigured } from "@rtas/utils/server/prisma";
