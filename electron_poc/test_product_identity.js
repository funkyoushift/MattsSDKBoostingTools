"use strict";
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

if (!process.versions.electron) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "msbt-branding-"));
  try {
    for (const mode of ["default", "override"]) {
      const run = spawnSync(require("electron"), [__filename, root, mode], {encoding:"utf8", timeout:30000});
      process.stdout.write(run.stdout || "");
      process.stderr.write(run.stderr || "");
      assert.equal(run.status, 0, run.error?.message || mode);
    }
  } finally { fs.rmSync(root, {recursive:true, force:true}); }
} else {
  const { app } = require("electron");
  const { PRODUCT_NAME, applyProductIdentity } = require("./product_identity");
  const pkg = require("./package.json");
  assert.equal(pkg.name, "matts-sdk-boosting-tools");
  app.setPath("appData", process.argv[2]);
  app.setName(pkg.name);
  if (process.argv[3] === "override") {
    const custom = path.join(process.argv[2], "custom");
    fs.mkdirSync(custom);
    app.setPath("userData", custom);
  }
  const before = {userData:app.getPath("userData"), sessionData:app.getPath("sessionData")};
  fs.mkdirSync(before.userData, {recursive:true});
  const saved = path.join(before.userData, "settings-sentinel.json");
  fs.writeFileSync(saved, '{"paired":true}');
  applyProductIdentity(app);
  assert.equal(app.getName(), PRODUCT_NAME);
  assert.equal(app.getPath("userData"), before.userData);
  assert.equal(app.getPath("sessionData"), before.sessionData);
  assert.equal(fs.readFileSync(path.join(app.getPath("userData"), "settings-sentinel.json"), "utf8"), '{"paired":true}');
  assert.equal(pkg.build.appId, "com.funkyoushift.msbt");
  assert.equal(pkg.build.executableName, "MattsSDKBoostingTools");
  assert.equal(pkg.build.productName, PRODUCT_NAME);
  assert.equal(pkg.build.nsis.shortcutName, PRODUCT_NAME);
  const {applyTutorialCopyOverlay} = require("./remote_data_catalogs");
  const tours = {main:[{title:"placeholder"}]};
  applyTutorialCopyOverlay(tours, {tours:{main:[{index:0,title:"Welcome to MSBT"}]}});
  assert.equal(tours.main[0].title, "Welcome to Borderlands 4 Modding Tools");
  console.log(`PASS product identity preserves ${process.argv[3]} profile/session and legacy overlay compatibility`);
  app.exit(0);
}
