const STORAGE_KEY = "rtas_device_fingerprint";

function hashString(input: string): string {
  let h = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `rtas_${(h >>> 0).toString(16)}`;
}

function collectSignals(): string {
  if (typeof window === "undefined") return "server";

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  let canvasData = "no-canvas";
  if (ctx) {
    ctx.textBaseline = "top";
    ctx.font = "16px Arial";
    ctx.fillStyle = "#f60";
    ctx.fillRect(0, 0, 120, 20);
    ctx.fillStyle = "#069";
    ctx.fillText("RTAS Studio AI", 2, 2);
    canvasData = canvas.toDataURL();
  }

  const parts = [
    navigator.userAgent,
    navigator.language,
    String(screen.width),
    String(screen.height),
    String(screen.colorDepth),
    String(new Date().getTimezoneOffset()),
    canvasData.slice(0, 120),
  ];

  return parts.join("|");
}

/** Lightweight stable browser fingerprint for free-tier anti-abuse */
export function getDeviceFingerprint(): string {
  if (typeof window === "undefined") return "";

  try {
    const cached = localStorage.getItem(STORAGE_KEY);
    if (cached) return cached;
    const fingerprint = hashString(collectSignals());
    localStorage.setItem(STORAGE_KEY, fingerprint);
    return fingerprint;
  } catch {
    return hashString(collectSignals());
  }
}
