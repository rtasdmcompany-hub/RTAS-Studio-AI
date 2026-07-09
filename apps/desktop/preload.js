const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("rtasDesktop", {
  platform: process.platform,
});
