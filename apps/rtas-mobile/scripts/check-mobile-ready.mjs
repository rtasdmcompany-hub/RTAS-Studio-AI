#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mobileRoot = path.resolve(__dirname, "..");

const required = [
  "capacitor.config.ts",
  "package.json",
  "www/index.html",
  "android/app/build.gradle",
  "android/gradlew.bat",
  "android/app/src/main/java/ai/rtasstudio/app/MainActivity.java",
  "ios/App/App/Info.plist",
  "assets/icons",
  "assets/splash",
  "scripts/prepare-mobile-assets.mjs",
];

const optionalMasters = [
  "assets/icons/logo-master.png",
  "assets/icons/icon-master.png",
  "assets/splash/splash-master.png",
];

let ok = true;

console.log("RTAS Mobile — readiness check\n");

for (const rel of required) {
  const full = path.join(mobileRoot, rel);
  const exists = fs.existsSync(full);
  console.log(`${exists ? "✓" : "✗"} ${rel}`);
  if (!exists) ok = false;
}

console.log("\nMaster artwork (drop before assets:generate):");
let hasMaster = false;
for (const rel of optionalMasters) {
  const full = path.join(mobileRoot, rel);
  if (fs.existsSync(full)) {
    console.log(`✓ ${rel}`);
    hasMaster = true;
  }
}
if (!hasMaster) {
  console.log("○ No master PNG yet — drop logo-master.png into assets/icons/");
}

try {
  const config = JSON.parse(
    fs.readFileSync(
      path.join(mobileRoot, "android/app/src/main/assets/capacitor.config.json"),
      "utf8"
    )
  );
  const url = config?.server?.url ?? "";
  console.log(`\nLive web hook: ${url || "(missing)"}`);
  if (url !== "https://rtas-studio-ai-web.vercel.app") ok = false;
} catch {
  console.log("\n✗ capacitor.config.json missing in Android assets");
  ok = false;
}

console.log(
  ok
    ? "\nStatus: READY for npm run mobile:android (Android Studio)"
    : "\nStatus: FIX missing items above before opening Android Studio"
);

process.exit(ok ? 0 : 1);
