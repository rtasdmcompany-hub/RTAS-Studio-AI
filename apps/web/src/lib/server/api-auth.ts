import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "@/lib/auth/auth-options";
import {
  getPersistentStoreMode,
  isPersistentStoreConfigured,
} from "@/lib/server/persistent-store";
import { Redis } from "@upstash/redis";

/** Require an authenticated NextAuth session. Returns 401 JSON when missing. */
export async function requireApiSession(options?: {
  requireEmailVerified?: boolean;
}) {
  const requireEmailVerified = options?.requireEmailVerified !== false;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return {
      ok: false as const,
      response: NextResponse.json(
        { error: "Authentication required." },
        { status: 401 }
      ),
    };
  }

  if (requireEmailVerified && session.user.emailVerified === false) {
    return {
      ok: false as const,
      response: NextResponse.json(
        {
          error: "Email verification required.",
          code: "EMAIL_NOT_VERIFIED",
        },
        { status: 403 }
      ),
    };
  }

  return { ok: true as const, session, userId: session.user.id };
}

/**
 * Admin routes — secret required in every deployed environment.
 * Local-only bypass: RTAS_ALLOW_OPEN_ADMIN=1 AND NODE_ENV=development.
 */
export function isAdminAuthorized(request: Request): boolean {
  const secret = process.env.RTAS_ADMIN_SECRET?.trim();
  if (!secret) {
    return (
      process.env.NODE_ENV === "development" &&
      process.env.RTAS_ALLOW_OPEN_ADMIN === "1"
    );
  }
  return request.headers.get("x-rtas-admin-secret") === secret;
}

export function adminUnauthorizedResponse() {
  return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
}

/** In-memory fallback (local/dev). Prefer Redis when KV is configured. */
const memoryBuckets = new Map<string, { count: number; resetAt: number }>();

let redisClient: Redis | null | undefined;

function getRateLimitRedis(): Redis | null {
  if (redisClient !== undefined) return redisClient;
  const url =
    process.env.KV_REST_API_URL?.trim() ||
    process.env.UPSTASH_REDIS_REST_URL?.trim() ||
    "";
  const token =
    process.env.KV_REST_API_TOKEN?.trim() ||
    process.env.UPSTASH_REDIS_REST_TOKEN?.trim() ||
    "";
  if (!url || !token) {
    redisClient = null;
    return null;
  }
  redisClient = new Redis({ url, token });
  return redisClient;
}

function memoryRateLimit(
  key: string,
  limit: number,
  windowMs: number
): { ok: true } | { ok: false; retryAfterSec: number } {
  const now = Date.now();
  const entry = memoryBuckets.get(key);
  if (!entry || entry.resetAt <= now) {
    memoryBuckets.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true };
  }
  if (entry.count >= limit) {
    return {
      ok: false,
      retryAfterSec: Math.max(1, Math.ceil((entry.resetAt - now) / 1000)),
    };
  }
  entry.count += 1;
  return { ok: true };
}

/**
 * Distributed rate limit when Redis/KV is configured; memory fallback otherwise.
 * On serverless without Redis, limits are best-effort per instance.
 */
export async function checkRateLimitAsync(
  key: string,
  limit: number,
  windowMs: number
): Promise<{ ok: true } | { ok: false; retryAfterSec: number }> {
  const redis = getRateLimitRedis();
  if (!redis) {
    return memoryRateLimit(key, limit, windowMs);
  }

  const redisKey = `rtas:rl:${key}`;
  const windowSec = Math.max(1, Math.ceil(windowMs / 1000));

  try {
    const count = await redis.incr(redisKey);
    if (count === 1) {
      await redis.expire(redisKey, windowSec);
    }
    if (count > limit) {
      const ttl = await redis.ttl(redisKey);
      return {
        ok: false,
        retryAfterSec: Math.max(1, ttl > 0 ? ttl : windowSec),
      };
    }
    return { ok: true };
  } catch {
    // Fail open to memory if Redis blips — reset client for next reconnect.
    redisClient = undefined;
    return memoryRateLimit(key, limit, windowMs);
  }
}

/** Sync wrapper for routes that cannot await (prefer checkRateLimitAsync). */
export function checkRateLimit(
  key: string,
  limit: number,
  windowMs: number
): { ok: true } | { ok: false; retryAfterSec: number } {
  return memoryRateLimit(key, limit, windowMs);
}

export function rateLimitResponse(retryAfterSec: number) {
  return NextResponse.json(
    { error: "Too many requests. Please try again shortly." },
    {
      status: 429,
      headers: { "Retry-After": String(retryAfterSec) },
    }
  );
}

export function clientIpFromRequest(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0]?.trim() ?? "";
  return request.headers.get("x-real-ip")?.trim() ?? "unknown";
}

export function rateLimitBackendHint(): string {
  return isPersistentStoreConfigured()
    ? getPersistentStoreMode()
    : "memory-fallback";
}
