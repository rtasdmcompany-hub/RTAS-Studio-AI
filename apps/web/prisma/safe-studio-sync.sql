-- Safe partial sync: add RTAS Studio tables without dropping existing Supabase tables.

DO $$ BEGIN
  CREATE TYPE "GenerationJobStatus" AS ENUM (
    'QUEUED',
    'GENERATING_CHUNKS',
    'COMPILING_MEDIA',
    'COMPLETED',
    'FAILED'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "passwordHash" TEXT,
    "image" TEXT,
    "provider" TEXT NOT NULL DEFAULT 'credentials',
    "emailVerified" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "tier" TEXT NOT NULL DEFAULT 'free',
    "credits" INTEGER NOT NULL DEFAULT 50,
    "concurrentTracks" INTEGER NOT NULL DEFAULT 0,
    "creditsExpireAt" TIMESTAMP(3),
    "subscriptionActive" BOOLEAN NOT NULL DEFAULT false,
    "subscriptionRenewsAt" TIMESTAMP(3),
    "freeTrialUsed" BOOLEAN NOT NULL DEFAULT false,
    "hasUsedFreeTrial" BOOLEAN NOT NULL DEFAULT false,
    "previewSkipsRemaining" INTEGER NOT NULL DEFAULT 3,
    "paymentProvider" TEXT,
    "externalCustomerId" TEXT,
    "externalSubscriptionId" TEXT,
    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "User_email_key" ON "User"("email");

CREATE TABLE IF NOT EXISTS "GenerationJob" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "status" "GenerationJobStatus" NOT NULL DEFAULT 'QUEUED',
    "prompt" TEXT,
    "inputImageUrl" TEXT,
    "generatedVideoUrl" TEXT,
    "durationSeconds" INTEGER NOT NULL DEFAULT 0,
    "creditsCharged" INTEGER NOT NULL DEFAULT 0,
    "chunkTotal" INTEGER,
    "chunksCompleted" INTEGER,
    "chunkManifest" JSONB,
    "errorMessage" TEXT,
    "backendJobId" TEXT,
    "isPublic" BOOLEAN NOT NULL DEFAULT false,
    "shareTitle" TEXT,
    "publishedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" TIMESTAMP(3),
    CONSTRAINT "GenerationJob_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "GenerationJob_userId_status_idx"
  ON "GenerationJob"("userId", "status");

CREATE INDEX IF NOT EXISTS "GenerationJob_userId_createdAt_idx"
  ON "GenerationJob"("userId", "createdAt" DESC);

CREATE INDEX IF NOT EXISTS "GenerationJob_isPublic_idx"
  ON "GenerationJob"("isPublic");

DO $$ BEGIN
  ALTER TABLE "GenerationJob"
    ADD CONSTRAINT "GenerationJob_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
