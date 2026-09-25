"use strict";
const assert = require("assert/strict");
const fs = require("fs/promises");
const path = require("path");
const os = require("os");
const oak = require("./oak2_install");
const { installPak } = require("./pak_install");
(async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-bundled-install-"));
  try {
    const root = path.join(dir, "game");
    await fs.mkdir(root);
    const options = { bundledZip: path.join(__dirname, "vendor/oak2/oak2-sdk.zip"),
      fetchImpl: () => { throw Error("Offline installation attempted network access"); } };
    const fresh = await oak.installOak2FromCache(dir, root, options);
    assert.equal(fresh.ok, true);
    const plugin = path.join(root, "OakGame/Binaries/Win64/Plugins");
    const runtime = path.join(plugin, "unrealsdk.dll");
    const manager = path.join(root, "sdk_mods/mods_base.sdkmod");
    for (const version of ["0.3", "0.4-beta.2", "1.0", "nightly-custom", "0.2"]) {
      await fs.writeFile(path.join(plugin, "unrealsdk.toml"), `[mod_manager]\ndisplay_version = "${version}"`);
      await fs.writeFile(runtime, `custom SDK ${version}`);
      await fs.writeFile(manager, `custom manager ${version}`);
      const result = await oak.installOak2FromCache(dir, root, options);
      assert.equal(result.preserved, true);
      assert.equal(result.ok, true);
      assert.equal(await fs.readFile(runtime, "utf8"), `custom SDK ${version}`);
      assert.equal(await fs.readFile(manager, "utf8"), `custom manager ${version}`);
    }
    await fs.unlink(manager);
    const partial = await oak.installOak2FromCache(dir, root, options);
    assert.equal(partial.ok, false);
    assert.equal(partial.preserved, true);
    assert.equal(await fs.readFile(runtime, "utf8"), "custom SDK 0.2");
    const bundle = path.join(__dirname, "../tools/third_party/afk_shift");
    const first = await installPak(bundle, root);
    assert.equal(first.installed, true);
    await fs.writeFile(first.destination, "previous user PAK");
    const replacement = await installPak(bundle, root);
    assert.equal(await fs.readFile(replacement.backup, "utf8"), "previous user PAK");
    assert.equal((await installPak(bundle, root)).unchanged, true);
    await fs.writeFile(path.join(dir, "bad.zip"), "bad archive");
    await assert.rejects(oak.ensureOak2ZipCached(dir, { bundledZip: path.join(dir, "bad.zip") }), /verification/);
    console.log("PASS: real offline SDK install, stable/beta/nightly preservation, partial install protection, PAK backup and verification");
  } finally { await fs.rm(dir, { recursive: true, force: true }); }
})().catch(e => { console.error(e); process.exitCode = 1; });
