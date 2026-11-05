"use strict";
const assert = require("assert/strict");
const fs = require("fs/promises");
const path = require("path");
const os = require("os");
const { createHash } = require("crypto");
const { installPak } = require("./pak_install");
const hash = s => createHash("sha256").update(s).digest("hex");
(async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-shift-install-"));
  try {
    const bundle = path.join(tmp, "bundle"), root = path.join(tmp, "game");
    const pakName = "pakchunk90-Windows_90_P.pak", modName = "ShiftManagement.sdkmod";
    await fs.mkdir(bundle, { recursive: true });
    await fs.writeFile(path.join(bundle, pakName), "pak");
    await fs.writeFile(path.join(bundle, modName), "companion");
    await fs.writeFile(path.join(bundle, "manifest.json"), JSON.stringify({ sha256: hash("pak"), companion_sha256: hash("companion") }));
    const pak = path.join(root, "OakGame", "Content", "Paks", pakName);
    const mods = path.join(root, "sdk_mods"), settings = path.join(mods, "settings");
    await fs.mkdir(path.dirname(pak), { recursive: true });
    await fs.writeFile(pak, "pak");
    await fs.mkdir(path.join(settings, "ShiftManagement"), { recursive: true });
    const protectedFile = path.join(settings, "ShiftManagement", "BL4_ShiftManagement_Settings_v1.json");
    await fs.writeFile(protectedFile, '{"protectedPlayers":["keep"]}');
    await fs.writeFile(path.join(settings, "ShiftManagement.json"), '{"other":"keep","enabled":false}');
    const first = await installPak(bundle, root);
    assert.equal(first.unchanged, false);
    assert.equal(await fs.readFile(first.companionDestination, "utf8"), "companion");
    assert.equal((JSON.parse(await fs.readFile(path.join(settings, "ShiftManagement.json")))).other, "keep");
    assert.equal((JSON.parse(await fs.readFile(path.join(settings, "ShiftManagement.json")))).enabled, true);
    assert.equal(await fs.readFile(protectedFile, "utf8"), '{"protectedPlayers":["keep"]}');
    await fs.writeFile(first.companionDestination, "old companion");
    const second = await installPak(bundle, root);
    assert.equal(await fs.readFile(second.companionBackup, "utf8"), "old companion");
    assert.equal((await installPak(bundle, root)).unchanged, true);
    await fs.writeFile(path.join(bundle, modName), "corrupt");
    await fs.writeFile(pak, "old pak");
    await assert.rejects(installPak(bundle, root), /verification/);
    assert.equal(await fs.readFile(pak, "utf8"), "old pak");
    assert.equal(await fs.readFile(protectedFile, "utf8"), '{"protectedPlayers":["keep"]}');
    // Fail after each committed write; restore byte-for-byte and preserve PAK inode.
    await fs.writeFile(path.join(bundle, modName), "companion");
    for (const failAfter of ["pak", "companion", "settings"]) {
      const testRoot = path.join(tmp, `rollback-${failAfter}`);
      const testPak = path.join(testRoot, "OakGame", "Content", "Paks", pakName);
      const testMods = path.join(testRoot, "sdk_mods");
      const testSettings = path.join(testMods, "settings", "ShiftManagement.json");
      const privateJson = path.join(testMods, "settings", "ShiftManagement", "BL4_ShiftManagement_Settings_v1.json");
      await fs.mkdir(path.dirname(testPak), { recursive: true });
      await fs.mkdir(path.dirname(privateJson), { recursive: true });
      await fs.writeFile(testPak, "original pak");
      const alias = path.join(tmp, `linked-${failAfter}`);
      await fs.link(testPak, alias);
      const inode = (await fs.stat(testPak)).ino;
      await fs.writeFile(path.join(testMods, modName), "original companion");
      await fs.writeFile(testSettings, '{"enabled":false,"other":"keep"}');
      await fs.writeFile(privateJson, '{"protectedPlayers":["private"]}');
      await assert.rejects(installPak(bundle, testRoot, { checkpoint: step => {
        if (step === failAfter) throw new Error("injected failure");
      }}), /injected failure/);
      assert.equal(await fs.readFile(testPak, "utf8"), "original pak");
      assert.equal(await fs.readFile(alias, "utf8"), "original pak");
      assert.equal((await fs.stat(testPak)).ino, inode);
      assert.equal(await fs.readFile(path.join(testMods, modName), "utf8"), "original companion");
      assert.equal(await fs.readFile(testSettings, "utf8"), '{"enabled":false,"other":"keep"}');
      assert.equal(await fs.readFile(privateJson, "utf8"), '{"protectedPlayers":["private"]}');
    }
    for (const failAfter of ["pak", "companion", "settings"]) {
      const fresh = path.join(tmp, `fresh-${failAfter}`);
      await assert.rejects(installPak(bundle, fresh, {checkpoint: step => {
        if (step === failAfter) throw new Error("injected failure");
      }}), /injected failure/);
      for (const file of [path.join(fresh,"OakGame","Content","Paks",pakName),
        path.join(fresh,"sdk_mods",modName), path.join(fresh,"sdk_mods","settings","ShiftManagement.json")]) {
        await assert.rejects(fs.stat(file), error => error.code === "ENOENT");
      }
    }
    // A cleanup failure must not turn a committed install into a false failure,
    // and must not hide a prior transactional error.
    const cleanupRoot = path.join(tmp, "cleanup-warning");
    let leftStage = "";
    const cleanupResult = await installPak(bundle, cleanupRoot, {cleanupStage: stage => {
      leftStage = stage; throw new Error("cleanup denied");
    }});
    assert.equal(cleanupResult.installed, true);
    assert.match(cleanupResult.warnings[0], /cleanup denied/);
    await fs.rm(leftStage, {recursive:true, force:true});
    const errorRoot = path.join(tmp, "cleanup-with-error");
    await assert.rejects(installPak(bundle, errorRoot, {
      checkpoint: () => { throw new Error("primary failure"); },
      cleanupStage: stage => { leftStage = stage; throw new Error("cleanup denied"); }
    }), error => /primary failure/.test(error.message) && /cleanup denied/.test(error.message));
    await fs.rm(leftStage, {recursive:true, force:true});
    console.log("PASS: cleanup warning preserves success and primary errors");
    console.log("PASS: hardlinked rollback and fresh-install rollback at each stage");
    console.log("PASS: companion install, backups, protected JSON, and preflight");
  } finally { await fs.rm(tmp, { recursive: true, force: true }); }
})().catch(error => { console.error(error); process.exitCode = 1; });
