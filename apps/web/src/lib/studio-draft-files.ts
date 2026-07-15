/**
 * Persist Studio draft file blobs in IndexedDB so refresh restores uploads.
 */

const DB_NAME = "rtas_studio_draft_files";
const DB_VERSION = 1;
const STORE = "files";

export type DraftFileRecord = {
  fieldId: string;
  name: string;
  mimeType: string;
  size: number;
  blob: Blob;
  updatedAt: string;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("indexedDB unavailable"));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "fieldId" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error ?? new Error("indexedDB open failed"));
  });
}

export async function saveDraftFile(
  fieldId: string,
  file: File
): Promise<void> {
  try {
    const db = await openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("save failed"));
      tx.objectStore(STORE).put({
        fieldId,
        name: file.name,
        mimeType: file.type || "application/octet-stream",
        size: file.size,
        blob: file,
        updatedAt: new Date().toISOString(),
      } satisfies DraftFileRecord);
    });
    db.close();
  } catch {
    /* private mode / quota */
  }
}

export async function removeDraftFile(fieldId: string): Promise<void> {
  try {
    const db = await openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("delete failed"));
      tx.objectStore(STORE).delete(fieldId);
    });
    db.close();
  } catch {
    /* ignore */
  }
}

export async function loadAllDraftFiles(): Promise<DraftFileRecord[]> {
  try {
    const db = await openDb();
    const rows = await new Promise<DraftFileRecord[]>((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).getAll();
      req.onsuccess = () => resolve((req.result as DraftFileRecord[]) ?? []);
      req.onerror = () => reject(req.error ?? new Error("load failed"));
    });
    db.close();
    return rows;
  } catch {
    return [];
  }
}

export async function clearAllDraftFiles(): Promise<void> {
  try {
    const db = await openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error ?? new Error("clear failed"));
      tx.objectStore(STORE).clear();
    });
    db.close();
  } catch {
    /* ignore */
  }
}

export function draftFileToFileField(record: DraftFileRecord): {
  file: File;
  name: string;
  mimeType: string;
  size: number;
} {
  const file = new File([record.blob], record.name, {
    type: record.mimeType,
    lastModified: Date.parse(record.updatedAt) || Date.now(),
  });
  return {
    file,
    name: record.name,
    mimeType: record.mimeType,
    size: record.size,
  };
}
