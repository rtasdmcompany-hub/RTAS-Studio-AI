#!/usr/bin/env node
/**
 * Stages master artwork from assets/icons/ and assets/splash/
 * into the flat paths expected by @capacitor/assets.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mobileRoot = path.resolve(__dirname, "..");
const assetsRoot = path.join(mobileRoot, "assets");
const iconsDir = path.join(assetsRoot, "icons");
const splashDir = path.join(assetsRoot, "splash");

const IMAGE_EXT = [".png", ".jpg", ".jpeg", ".svg"];

function findMaster(dir, baseNames) {
  for (const base of baseNames) {
    for (const ext of IMAGE_EXT) {
      const candidate = path.join(dir, `${base}${ext}`);
      if (fs.existsSync(candidate)) return candidate;
    }
  }
  return null;
}

function copyMaster(source, destName) {
  const dest = path.join(assetsRoot, destName);
  fs.copyFileSync(source, dest);
  return dest;
}

function extOf(filePath) {
  return path.extname(filePath).toLowerCase();
}

function stageAs(source, destBase) {
  const dest = path.join(assetsRoot, `${destBase}${extOf(source)}`);
  fs.copyFileSync(source, dest);
  return dest;
}

const logoMaster = findMaster(iconsDir, [
  "logo-master",
  "logo",
  "rtas-logo",
  "icon-master",
]);
const iconMaster = findMaster(iconsDir, ["icon-master", "icon-only", "app-icon"]);
const splashMaster = findMaster(splashDir, [
  "splash-master",
  "splash",
  "rtas-splash",
]);

const staged = [];

if (iconMaster && splashMaster) {
  staged.push(stageAs(iconMaster, "icon-only"));
  staged.push(stageAs(splashMaster, "splash"));
  console.log("[assets] Full-control mode: icon + splash masters detected.");
} else if (logoMaster) {
  staged.push(stageAs(logoMaster, "logo"));
  console.log("[assets] Easy mode: single logo master detected.");
} else if (iconMaster) {
  staged.push(stageAs(iconMaster, "logo"));
  console.log("[assets] Easy mode: icon master used as logo source.");
} else {
  console.error(
    [
      "[assets] No master artwork found.",
      "",
      "Drop one of the following, then re-run assets:generate:",
      "  • assets/icons/logo-master.png   (1024×1024+, easy mode — icon + splash)",
      "  • assets/icons/icon-master.png   (1024×1024+) + assets/splash/splash-master.png (2732×2732+)",
      "",
      "Supported formats: PNG, JPG, SVG",
    ].join("\n")
  );
  process.exit(1);
}

const darkLogo = findMaster(iconsDir, ["logo-dark-master", "logo-dark"]);
if (darkLogo) {
  staged.push(stageAs(darkLogo, "logo-dark"));
}

const darkSplash = findMaster(splashDir, ["splash-dark-master", "splash-dark"]);
if (darkSplash) {
  staged.push(stageAs(darkSplash, "splash-dark"));
}

console.log("[assets] Staged files:");
for (const file of staged) {
  console.log(`  → ${path.relative(mobileRoot, file)}`);
}
