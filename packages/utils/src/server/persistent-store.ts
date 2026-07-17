import { promises as fs } from "fs";
import path from "path";
import { Redis } from "@upstash/redis";
import { isServerlessRuntime } from "./data-dir";

const STORE_PREFIX = "rtas:";
const LOCAL_DATA_DIR = path.join(process.cwd(), ".data");

export class PersistentStoreNotConfiguredError extends Error {
  constructor() {
    super(
      "Persistent storage is not configured for Vercel. " +
        "Add Vercel KV (or Upstash Redis) and set KV_REST_API_URL + KV_REST_API_TOKEN " +
        "in your Vercel project environment variables."
    );
    this.name = "PersistentStoreNotConfiguredError";
  }
}

type RedisClient = Redis;

let redisClient: RedisClient | null | undefined;

function getRedisRestConfig(): { url: string; token: string } | null {
  const url =
    process.env.KV_REST_API_URL?.trim() ||
    process.env.UPSTASH_REDIS_REST_URL?.trim() ||
    "";
  const token =
    process.env.KV_REST_API_TOKEN?.trim() ||
    process.env.UPSTASH_REDIS_REST_TOKEN?.trim() ||
    "";
  if (!url || !token) return null;
  return { url, token };
}

const memoryDocuments = new Map<string, unknown>();

/** Temporary RC / infra gate: allow in-memory store until Upstash/KV is linked. */
function isMemoryStoreAllowed(): boolean {
  const v = process.env.RTAS_ALLOW_MEMORY_STORE?.trim().toLowerCase();
  return v === "1" || v === "true";
}

export function isPersistentStoreConfigured(): boolean {
  return getRedisRestConfig() !== null || isMemoryStoreAllowed();
}

export function getPersistentStoreMode(): "redis" | "memory" | "local-file" {
  if (getRedisRestConfig()) return "redis";
  if (isMemoryStoreAllowed()) return "memory";
  return "local-file";
}

function getRedis(): RedisClient | null {
  if (redisClient !== undefined) return redisClient;

  const config = getRedisRestConfig();
  if (!config) {
    redisClient = null;
    return null;
  }

  redisClient = new Redis({ url: config.url, token: config.token });
  return redisClient;
}

function storeKey(name: string): string {
  return `${STORE_PREFIX}${name}`;
}

function localFilePath(name: string): string {
  const safe = name.replace(/[^a-zA-Z0-9._-]/g, "_");
  return path.join(LOCAL_DATA_DIR, `${safe}.json`);
}

async function readLocalJson<T>(name: string, fallback: T): Promise<T> {
  try {
    await fs.mkdir(LOCAL_DATA_DIR, { recursive: true });
    const raw = await fs.readFile(localFilePath(name), "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

async function writeLocalJson<T>(name: string, data: T): Promise<void> {
  await fs.mkdir(LOCAL_DATA_DIR, { recursive: true });
  await fs.writeFile(localFilePath(name), JSON.stringify(data, null, 2), "utf-8");
}

function assertServerlessPersistence(): void {
  if (isServerlessRuntime() && !isPersistentStoreConfigured()) {
    throw new PersistentStoreNotConfiguredError();
  }
}

/** Read a named JSON document (auth-users, profiles, etc.). */
export async function readJsonDocument<T>(name: string, fallback: T): Promise<T> {
  const redis = getRedis();
  if (redis) {
    const value = await redis.get<T>(storeKey(name));
    return value ?? fallback;
  }

  if (isMemoryStoreAllowed()) {
    const key = storeKey(name);
    if (!memoryDocuments.has(key)) return fallback;
    return memoryDocuments.get(key) as T;
  }

  if (isServerlessRuntime()) {
    assertServerlessPersistence();
  }

  return readLocalJson(name, fallback);
}

/** Write a named JSON document atomically. */
export async function writeJsonDocument<T>(name: string, data: T): Promise<void> {
  const redis = getRedis();
  if (redis) {
    await redis.set(storeKey(name), data);
    return;
  }

  if (isMemoryStoreAllowed()) {
    memoryDocuments.set(storeKey(name), data);
    return;
  }

  if (isServerlessRuntime()) {
    assertServerlessPersistence();
  }

  await writeLocalJson(name, data);
}
