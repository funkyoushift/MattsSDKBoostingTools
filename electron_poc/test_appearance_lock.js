"use strict";

/**
 * Guardrail: the desktop panel must keep its designed dark palette when
 * Windows light mode or Contrast / High Contrast themes are on.
 * Run with: node test_appearance_lock.js
 */
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const root = __dirname;
const mainJs = fs.readFileSync(path.join(root, "main.js"), "utf8");
const stylesCss = fs.readFileSync(path.join(root, "styles.css"), "utf8");
const rendererHtml = fs.readFileSync(path.join(root, "renderer.html"), "utf8");

assert.match(mainJs, /nativeTheme/, "main.js must import nativeTheme");
assert.match(
  mainJs,
  /nativeTheme\.themeSource\s*=\s*["']dark["']/,
  "main.js must pin nativeTheme.themeSource to dark before windows open"
);
assert.match(
  mainJs,
  /ForcedColors/,
  "main.js must disable Chromium ForcedColors so Windows Contrast themes cannot remap UA chrome"
);
assert.match(
  mainJs,
  /appendSwitch\(\s*["']disable-features["']/,
  "main.js must pass ForcedColors through Chromium disable-features"
);
assert.match(
  mainJs,
  /backgroundMaterial:\s*["']none["']/,
  "BrowserWindow must not use Mica/Acrylic wallpaper material"
);

assert.match(stylesCss, /color-scheme:\s*dark only/, "styles.css must opt out of light UA styling");
assert.match(stylesCss, /forced-color-adjust:\s*none/, "styles.css must keep author colors under forced-colors");
assert.match(
  rendererHtml,
  /<meta\s+name="color-scheme"\s+content="dark only">/,
  "renderer.html must declare dark-only color-scheme"
);

console.log("appearance lock ok");
