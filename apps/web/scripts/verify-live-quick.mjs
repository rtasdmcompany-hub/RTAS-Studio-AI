import { chromium } from "playwright";

const BASE = "https://rtas-studio-ai-web.vercel.app";
const VIEWPORTS = [390, 768, 1024, 1280, 1366, 1440, 1920];
const PAGES = [
  "/features", "/pricing", "/docs", "/help", "/showcase", "/developers",
  "/careers", "/blog", "/status", "/privacy", "/terms", "/cookies",
  "/about", "/how-to-use",
];
const NAV_TIMEOUT = 45_000;

function filterConsole(msg) {
  const t = msg.text();
  if (/favicon|devtools|Download the React DevTools/i.test(t)) return null;
  if (msg.type() === "error") return t;
  return null;
}

async function measureHome(page, width) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
  await page.waitForTimeout(800);
  return page.evaluate(() => {
    const docEl = document.documentElement;
    const clientWidth = docEl.clientWidth;
    const scrollWidth = docEl.scrollWidth;
    const header =
      document.querySelector("header") ||
      document.querySelector("[data-site-header]") ||
      document.querySelector(".rtas-header") ||
      document.querySelector("nav");
    let headerMaxRight = 0;
    let headerClip = false;
    if (header) {
      const kids = header.querySelectorAll(":scope > *");
      const nodes = kids.length ? kids : header.children;
      for (const el of nodes) {
        const r = el.getBoundingClientRect();
        headerMaxRight = Math.max(headerMaxRight, r.right);
        if (r.right > clientWidth + 1) headerClip = true;
      }
      // also check descendants that might overflow
      for (const el of header.querySelectorAll("*")) {
        const r = el.getBoundingClientRect();
        if (r.right > clientWidth + 1) {
          headerMaxRight = Math.max(headerMaxRight, r.right);
          headerClip = true;
        }
      }
    }
    return {
      clientWidth,
      scrollWidth,
      horizontalOverflow: scrollWidth > clientWidth + 1,
      overflowDelta: scrollWidth - clientWidth,
      headerMaxRight,
      headerClip,
    };
  });
}

async function bgAt1440(page) {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
  await page.waitForTimeout(800);
  return page.evaluate(() => {
    const selA = ".rtas-hero-showcase__content.video-text-highlight";
    const selB = ".rtas-landing-outcomes";
    const a = document.querySelector(selA);
    const b = document.querySelector(selB);
    return {
      heroContent: a ? getComputedStyle(a).backgroundColor : null,
      landingOutcomes: b ? getComputedStyle(b).backgroundColor : null,
      found: { heroContent: !!a, landingOutcomes: !!b },
    };
  });
}

async function main() {
  const consoleErrors = [];
  const issues = [];
  const report = {
    base: BASE,
    checkedAt: new Date().toISOString(),
    viewports: {},
    backgrounds1440: null,
    pages: {},
    studio: null,
    consoleErrors: [],
    issues: [],
  };

  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultNavigationTimeout(NAV_TIMEOUT);
  page.on("console", (msg) => {
    const e = filterConsole(msg);
    if (e) consoleErrors.push(e);
  });
  page.on("pageerror", (err) => {
    const t = String(err?.message || err);
    if (!/favicon|devtools/i.test(t)) consoleErrors.push(t);
  });

  try {
    for (const w of VIEWPORTS) {
      try {
        const m = await measureHome(page, w);
        report.viewports[String(w)] = m;
        if (m.horizontalOverflow) issues.push(`Horizontal overflow on ${w} (${m.scrollWidth}>${m.clientWidth})`);
        if (m.headerClip) issues.push(`Header clip/overflow on ${w}`);
      } catch (err) {
        report.viewports[String(w)] = { error: String(err?.message || err) };
        issues.push(`Viewport ${w} failed: ${err?.message || err}`);
      }
    }

    try {
      report.backgrounds1440 = await bgAt1440(page);
    } catch (err) {
      report.backgrounds1440 = { error: String(err?.message || err) };
    }

    for (const path of PAGES) {
      try {
        const res = await page.goto(BASE + path, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
        const status = res ? res.status() : null;
        report.pages[path] = { status, url: page.url() };
        if (status != null && status >= 400) issues.push(`${path} status ${status}`);
      } catch (err) {
        report.pages[path] = { error: String(err?.message || err) };
        issues.push(`${path} nav failed: ${err?.message || err}`);
      }
    }

    try {
      const res = await page.goto(BASE + "/studio", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
      report.studio = { status: res ? res.status() : null, finalUrl: page.url() };
      if (report.studio.status != null && report.studio.status >= 400) {
        issues.push(`/studio status ${report.studio.status}`);
      }
    } catch (err) {
      report.studio = { error: String(err?.message || err) };
      issues.push(`/studio nav failed: ${err?.message || err}`);
    }
  } finally {
    await browser.close();
  }

  report.consoleErrors = [...new Set(consoleErrors)];
  report.issues = issues;
  console.log(JSON.stringify(report, null, 2));
  if (issues.some((i) => /Horizontal overflow|Header clip|status \d{3}/i.test(i)) || issues.some((i) => /status \d{3}/.test(i))) {
    // exit 1 if any horizontal overflow or header clip or status>=400
    const fail =
      issues.some((i) => i.includes("Horizontal overflow") || i.includes("Header clip")) ||
      issues.some((i) => /status [4-5]\d\d/.test(i));
    process.exit(fail ? 1 : 0);
  }
  const fail =
    Object.values(report.viewports).some((v) => v?.horizontalOverflow || v?.headerClip) ||
    Object.values(report.pages).some((p) => p?.status >= 400) ||
    (report.studio?.status >= 400);
  process.exit(fail ? 1 : 0);
}

main().catch((err) => {
  console.error(JSON.stringify({ fatal: String(err?.message || err) }, null, 2));
  process.exit(1);
});
