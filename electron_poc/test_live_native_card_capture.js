"use strict";

// Manual integration check: pass a widget JSON captured from the current game
// and an output PNG path. The input remains outside the repository.
const fs = require("node:fs");
const {app, BrowserWindow, protocol} = require("electron");
const nativeProtocol = require("./native_card_protocol");
nativeProtocol.registerNativeCardSchemes(protocol);

app.whenReady().then(async () => {
  const [widgetPath, imagePath] = process.argv.slice(2);
  if (!widgetPath || !imagePath) throw new Error("Pass widget JSON and output PNG paths");
  nativeProtocol.installNativeCardProtocol(protocol);
  const widget = JSON.parse(fs.readFileSync(widgetPath, "utf8"));
  const result = await require("./native_card_capture").captureNativeWidget(BrowserWindow, widget);
  if (!result.ok || !result.base64 || result.width < 100 || result.height < 100)
    throw new Error("Live widget did not produce a complete card image");
  fs.writeFileSync(imagePath, Buffer.from(result.base64, "base64"));
  console.log(JSON.stringify({ok:true, width:result.width, height:result.height,
    imageBytes:fs.statSync(imagePath).size, warnings:result.warnings}));
  app.exit(0);
}).catch(error => {
  console.error(String(error.stack || error));
  app.exit(1);
});
