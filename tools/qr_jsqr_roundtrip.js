"use strict";
const fs = require("fs");
const path = require("path");
const jsQR = require(path.join(
  __dirname,
  "..",
  "mobile_controller",
  "app",
  "src",
  "main",
  "assets",
  "jsQR.min.js"
));

const matrixPath = process.argv[2];
const payloadPath = process.argv[3];
if (!matrixPath || !payloadPath) {
  console.error("usage: node qr_jsqr_roundtrip.js matrix.json payload.txt");
  process.exit(2);
}

const matrix = JSON.parse(fs.readFileSync(matrixPath, "utf8"));
const expected = fs.readFileSync(payloadPath, "utf8");
const scale = 8;
const quiet = 4;
const n = matrix.length;
const width = (n + quiet * 2) * scale;
const data = new Uint8ClampedArray(width * width * 4);
data.fill(255);
for (let i = 3; i < data.length; i += 4) data[i] = 255;
for (let y = 0; y < n; y += 1) {
  for (let x = 0; x < n; x += 1) {
    const dark = matrix[y][x] ? 0 : 255;
    for (let dy = 0; dy < scale; dy += 1) {
      for (let dx = 0; dx < scale; dx += 1) {
        const idx = (((y + quiet) * scale + dy) * width + ((x + quiet) * scale + dx)) * 4;
        data[idx] = dark;
        data[idx + 1] = dark;
        data[idx + 2] = dark;
        data[idx + 3] = 255;
      }
    }
  }
}
const result = jsQR(data, width, width, { inversionAttempts: "attemptBoth" });
if (!result || result.data !== expected) {
  console.error("DECODE_FAIL", result && result.data);
  process.exit(1);
}
console.log("DECODE_OK", result.data.length);
