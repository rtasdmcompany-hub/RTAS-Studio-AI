/**
 * Live production verification for RTAS Studio AI Phase 1.
 * Run: node scripts/verify-live-production.mjs
 */
import { chromium } from "playwright";

const BASE = process.env.VERIFY_URL || "https://rtas-studio-ai-web.vercel.app";

const VIEWPORTS = [
  { name: "1024", width: 1024, height: 768 },
  { name: "1280", width: 1280, height: 800 },
  { name: "1366", width: 1366, height: 768 },
  { name: "1440", width: 1440, height: 900 },
  { name: "1600", width: 1600, height: 900 },
  { name: "1920", width: 1920, height: 1080 },
  { name: "4K", width: 3840, height: 2160 },
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
];

const NAV_ROUTES = [
  "/studio",
  "/profile",
  "/showcase",
  "/features",
  "/pricing",
  "/docs",
  "/help",
];

const FOOTER_SAMPLE = [
  "/docs",
  "/developers",
  "/careers",
  "/blog",
  "/status",
  "/privacy",
  "/terms",
  "/cookies",
  "/about",
];

function collectIssues() {
  return [];
}

async function measureOverflow(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    const scrollW = Math.max(doc.scrollWidth, body.scrollWidth);
    const clientW = doc.clientWidth;
    const header = document.querySelector(".rtas-header, header");
    let headerOverflow = false;
    let headerClipped = false;
    if (header) {
      const hr = header.getBoundingClientRect();
      headerOverflow = header.scrollWidth > header.clientWidth + 1;
      // any child past viewport right edge
      const children = header.querySelectorAll("*");
      for (const el of children) {
        const r = el.getBoundingClientRect();
        if (r.right > clientW + 2) {
          headerClipped = true;
          break;
        }
      }
      if (hr.right > clientW + 2) headerClipped = true;
    }
    return {
      horizontalOverflow: scrollW > clientW + 2,
      scrollWidth: scrollW,
      clientWidth: clientW,
      headerOverflow,
      headerClipped,
      hasDensityClass: Boolean(
        document.querySelector(
          ".rtas-header--density-full, .rtas-header--density-comfortable, .rtas-header--density-compact, .rtas-header--density-tight, .rtas-header--drawer-nav"
        )
      ),
    };
  });
}

async function landingContrast(page) {
  return page.evaluate(() => {
    const hero = document.querySelector(
      ".rtas-hero-showcase__content.video-text-highlight, .video-text-highlight"
    );
    const panel = document.querySelector(
      ".rtas-landing-outcomes.video-content-panel, .video-content-panel"
    );
    const readBg = (el) => {
      if (!el) return null;
      const s = getComputedStyle(el);
      return { bg: s.backgroundColor, opacity: s.opacity };
    };
    return {
      hero: readBg(hero),
      panel: readBg(panel),
      outcomesTitle: document.querySelector(".rtas-landing-outcomes__title")
        ?.textContent,
    };
  });
}

async function studioWizardState(page) {
  return page.evaluate(() => {
    const guided = Boolean(
      document.querySelector(".studio-create-experience--guided")
    );
    const projectTitle = Boolean(
      document.querySelector("#studio-project-title")
    );
    const templateDump = document.querySelectorAll(".studio-template-grid .studio-template-card").length;
    const projectCards = document.querySelectorAll(".studio-project-card").length;
    const activeSteps = document.querySelectorAll(
      ".studio-guided-step.is-active"
    ).length;
    const welcomeQuick = document.querySelectorAll(".studio-quick-grid .studio-quick-card").length;
    return {
      guided,
      projectTitle,
      templateDump,
      projectCards,
      activeSteps,
      welcomeQuick,
      bodyText: document.body?.innerText?.slice(0, 400) || "",
    };
  });
}

async function main() {
  const issues = collectIssues();
  const report = {
    base: BASE,
    checkedAt: new Date().toISOString(),
    viewports: {},
    routes: {},
    footer: {},
    studio: null,
    landing: null,
    console: { errors: [], warnings: [] },
    issues: [],
  };

  const browser = await chromium.launch({
    headless: true,
    channel: process.env.VERIFY_CHANNEL || "msedge",
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });

  try {
    const context = await browser.newContext();
    const page = await context.newPage();

    page.on("console", (msg) => {
      const type = msg.type();
      const text = msg.text();
      if (type === "error") report.console.errors.push(text);
      if (type === "warning" && /hydrat|React/i.test(text)) {
        report.console.warnings.push(text);
      }
    });
    page.on("pageerror", (err) => {
      report.console.errors.push(String(err));
    });

    // Landing + viewport matrix
    for (const vp of VIEWPORTS) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(800);
      const overflow = await measureOverflow(page);
      report.viewports[vp.name] = overflow;
      if (overflow.horizontalOverflow) {
        issues.push(`Horizontal overflow on ${vp.name} (${overflow.scrollWidth}>${overflow.clientWidth})`);
      }
      if (overflow.headerClipped || overflow.headerOverflow) {
        issues.push(`Header clip/overflow on ${vp.name}`);
      }
    }

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 90000 }).catch(() => {});
    report.landing = await landingContrast(page);
    const heroBg = report.landing?.hero?.bg || "";
    // Expect dark overlay: rgba with alpha roughly >= 0.7 or rgb near black
    if (heroBg.includes("rgba")) {
      const m = heroBg.match(/rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*([0-9.]+)\s*\)/);
      if (m && Number(m[1]) < 0.7) {
        issues.push(`Hero overlay too light: ${heroBg}`);
      }
    }

    // Nav routes
    for (const route of NAV_ROUTES) {
      const res = await page.goto(BASE + route, {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
      report.routes[route] = {
        status: res?.status() ?? null,
        finalUrl: page.url(),
      };
      const status = res?.status() ?? 0;
      if (status >= 400) issues.push(`Nav route ${route} returned ${status}`);
    }

    // Footer sample pages
    for (const route of FOOTER_SAMPLE) {
      const res = await page.goto(BASE + route, {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
      report.footer[route] = {
        status: res?.status() ?? null,
        finalUrl: page.url(),
      };
      const status = res?.status() ?? 0;
      if (status >= 400) issues.push(`Footer route ${route} returned ${status}`);
    }

    // Studio wizard (may redirect to auth)
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE + "/studio", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForTimeout(1500);
    report.studio = {
      url: page.url(),
      ...(await studioWizardState(page)),
    };

    if (report.studio.url.includes("/studio")) {
      if (!report.studio.guided && !report.studio.projectTitle) {
        // Might still be loading skeleton / auth
        if (!/sign|login|auth|loading/i.test(report.studio.bodyText)) {
          issues.push("Studio guided wizard markers not found on /studio");
        }
      }
      if (report.studio.templateDump > 10) {
        issues.push(
          `Studio still dumps ${report.studio.templateDump} template cards`
        );
      }
      if (report.studio.welcomeQuick > 6 && report.studio.projectCards === 0) {
        issues.push("Studio still shows large quick-start grid without project cards");
      }
    }

    // Filter noisy console (third-party)
    report.console.errors = [...new Set(report.console.errors)].filter(
      (e) =>
        !/favicon|Download the React DevTools|third-party|chrome-extension/i.test(
          e
        )
    );
    if (report.console.errors.length) {
      issues.push(`Console errors: ${report.console.errors.slice(0, 5).join(" | ")}`);
    }
    if (report.console.warnings.some((w) => /hydrat/i.test(w))) {
      issues.push("Hydration warning detected in console");
    }

    report.issues = issues;
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify(report, null, 2));
  if (issues.length) {
    console.error(`\nFAILED with ${issues.length} issue(s)`);
    process.exitCode = 1;
  } else {
    console.error("\nPASSED live verification");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
