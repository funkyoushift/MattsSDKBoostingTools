const { EventEmitter } = require("events");
const fs = require("fs");
const path = require("path");
const { execFile, spawn } = require("child_process");

function prepareRunner(setupPath) {
  if (!process.env.LOCALAPPDATA) throw new Error("Windows local application data folder is unavailable.");
  const folder = path.join(process.env.LOCALAPPDATA, "Programs", "MSBT");
  fs.mkdirSync(folder, { recursive: true });
  const runFolder = fs.mkdtempSync(path.join(folder, "update-"));
  const runner = path.join(runFolder, "MSBT-Update.exe");
  // Run outside app/: Windows must be able to replace the entire app directory.
  fs.copyFileSync(setupPath, runner);
  return runner;
}

// The exact same setup binary handles first install and every subsequent update.
class PersistentUpdater extends EventEmitter {
  constructor({ setupPath, app, isNewer, run = execFile, start = spawn, prepare = prepareRunner, installedVersions = () => [app.getVersion()] }) {
    super();
    Object.assign(this, { setupPath, app, isNewer, run, start, prepare, installedVersions });
    this.ready = false;
    this.busy = false;
  }
  invoke(mode) {
    return new Promise((resolve, reject) => {
      this.run(this.setupPath, [mode], { windowsHide: true, timeout: 35 * 60 * 1000, maxBuffer: 65536 }, (error, stdout, stderr) => {
        if (error) return reject(new Error(String(stderr || error.message).trim()));
        try {
          const info = JSON.parse(stdout);
          if (!info.ok || !/^\d+\.\d+\.\d+(\.\d+)?$/.test(info.version)) throw new Error("Setup returned an invalid release version.");
          resolve(info);
        } catch (parseError) { reject(parseError); }
      });
    });
  }
  async checkForUpdates() {
    if (this.busy) return { updateInfo: this.info };
    this.emit("checking-for-update");
    const info = await this.invoke("--check");
    if (this.ready && info.version !== this.info.version) this.ready = false;
    this.info = info;
    this.emit(this.ready ? "update-downloaded" : (!this.isNewer(this.app.getVersion(), info.version) && this.installedVersions().some(version => this.isNewer(info.version, version))) ? "update-available" : "update-not-available", info);
    return { updateInfo: info };
  }
  async downloadUpdate() {
    if (this.busy) throw new Error("An update is already downloading.");
    this.busy = true;
    this.ready = false;
    this.emit("download-progress", { percent: 0 });
    try {
      this.info = await this.invoke("--download");
      this.ready = true;
      this.emit("update-downloaded", this.info);
      return [this.setupPath];
    } finally { this.busy = false; }
  }
  quitAndInstall() {
    if (!this.ready) throw new Error("Download the update first.");
    const runner = this.prepare(this.setupPath);
    return new Promise((resolve, reject) => {
      const child = this.start(runner, ["--apply", "--wait-pid", String(process.pid)], { cwd: path.dirname(runner), detached: true, stdio: "ignore" });
      child.once("error", reject);
      child.once("spawn", () => { child.unref(); resolve(); this.app.quit(); });
    });
  }
}

function findSetup(resourcesPath) {
  const setup = path.join(resourcesPath, "setup", "MSBT-Setup.exe");
  return fs.existsSync(setup) ? setup : null;
}
module.exports = { PersistentUpdater, findSetup, prepareRunner };
