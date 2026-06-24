import type { CapacitorConfig } from "@capacitor/cli";

/** Live production web app — mobile shell loads this URL in the native WebView. */
const PRODUCTION_WEB_URL = "https://rtas-studio-ai-web.vercel.app";

const config: CapacitorConfig = {
  appId: "ai.rtasstudio.app",
  appName: "RTAS Studio AI",
  webDir: "www",
  server: {
    url: PRODUCTION_WEB_URL,
    androidScheme: "https",
    iosScheme: "https",
    cleartext: false,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2200,
      launchAutoHide: true,
      backgroundColor: "#0a0a0f",
      androidSplashResourceName: "splash",
      androidScaleType: "CENTER_CROP",
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: "DARK",
      backgroundColor: "#0a0a0f",
    },
  },
  ios: {
    contentInset: "automatic",
    scrollEnabled: true,
    allowsLinkPreview: false,
    preferredContentMode: "mobile",
  },
  android: {
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: false,
  },
};

export default config;
