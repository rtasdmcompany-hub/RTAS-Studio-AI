import {
  readJsonDocument,
  writeJsonDocument,
} from "@/lib/server/persistent-store";

const STORE_NAME = "webhook-event-ids";

type WebhookEventFile = {
  events: Record<string, { provider: string; processedAt: string }>;
};

/**
 * Claim a webhook/payment event id for one-time processing (replay protection).
 * Returns true if this is the first claim; false if already processed.
 */
export async function claimWebhookEventId(
  eventId: string,
  provider: string
): Promise<boolean> {
  const id = (eventId || "").trim();
  if (!id) return true; // no id — caller should still validate payload carefully

  const store = await readJsonDocument<WebhookEventFile>(STORE_NAME, {
    events: {},
  });
  if (store.events[id]) {
    return false;
  }

  store.events[id] = {
    provider,
    processedAt: new Date().toISOString(),
  };

  // Bound growth — keep newest ~2000 events
  const keys = Object.keys(store.events);
  if (keys.length > 2000) {
    const sorted = keys.sort(
      (a, b) =>
        Date.parse(store.events[a].processedAt) -
        Date.parse(store.events[b].processedAt)
    );
    for (const drop of sorted.slice(0, keys.length - 2000)) {
      delete store.events[drop];
    }
  }

  await writeJsonDocument(STORE_NAME, store);
  return true;
}
