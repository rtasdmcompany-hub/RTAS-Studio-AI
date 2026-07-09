const { app, BrowserWindow, shell } = require("electron");
const path = require("node:path");

const DEFAULT_WEB_URL =
  process.env.WEB_APP_URL ||
  process.env.RTAS_WEB_URL ||
  "http://localhost:3000/studio";

const PRODUCTION_WEB_URL = "https://rtas-studio-ai-web.vercel.app/studio";

function resolveWebUrl() {
  if (process.env.NODE_ENV === "development") {
    return DEFAULT_WEB_URL;
  }
  return process.env.WEB_APP_URL || PRODUCTION_WEB_URL;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 640,
    backgroundColor: "#09090b",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const target = resolveWebUrl();
  win.loadURL(target);

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
