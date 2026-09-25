"use strict";
const fs = require("fs/promises");
const path = require("path");
const oak = require("../electron_poc/oak2_install");
(async () => {
  const destination = path.join(__dirname, "../electron_poc/vendor/oak2/oak2-sdk.zip");
  let valid = false;
  try { valid = await oak.sha256File(destination) === oak.OAK2_SHA256; } catch {}
  if (!valid) {
    const result = await oak.downloadToFile(oak.OAK2_DOWNLOAD_URL, destination);
    if (result.sha256 !== oak.OAK2_SHA256) throw Error("Official SDK hash mismatch");
  }
  const pakDir = path.join(__dirname, "third_party/afk_shift");
  const manifest = JSON.parse(await fs.readFile(path.join(pakDir, "manifest.json"), "utf8"));
  if (await oak.sha256File(path.join(pakDir, "pakchunk90-Windows_90_P.pak")) !== manifest.sha256) throw Error("AFK PAK hash mismatch");
  console.log("Verified bundled SDK and AFK SHiFT PAK.");
})().catch(e => { console.error(e); process.exitCode = 1; });
