const PRODUCTION_WEB_URL = "https://rtas-studio-ai-web.vercel.app";

function isLikelyNativeShell() {
  return (
    typeof window.Capacitor !== "undefined" ||
    /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
  );
}

function bootstrap() {
  const message = document.querySelector(".mobile-shell__message");

  if (isLikelyNativeShell()) {
    window.location.replace(PRODUCTION_WEB_URL);
    return;
  }

  if (message) {
    message.textContent =
      "Shell fallback — run via Capacitor on iOS/Android to load the live studio.";
  }
}

bootstrap();
