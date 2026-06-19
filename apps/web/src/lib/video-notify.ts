import type { GeneratedVideo, UserProfile } from "@rtas/shared";

export async function notifyVideoReady(
  profile: UserProfile,
  video: GeneratedVideo
): Promise<void> {
  try {
    await fetch("/api/notify/video-ready", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: profile.email,
        name: profile.name,
        title: video.title,
        videoUrl: video.videoUrl,
        durationSeconds: video.durationSeconds,
      }),
    });
  } catch {
    /* non-blocking */
  }

  if (typeof window === "undefined" || !("Notification" in window)) return;

  const show = () => {
    new Notification("RTAS Studio AI", {
      body: `Your video "${video.title}" is ready to watch.`,
      icon: "/rtas-favicon.png",
    });
  };

  if (Notification.permission === "granted") {
    show();
    return;
  }
  if (Notification.permission !== "denied") {
    const permission = await Notification.requestPermission();
    if (permission === "granted") show();
  }
}
