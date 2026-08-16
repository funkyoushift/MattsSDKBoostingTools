"use strict";

const { spawn } = require("child_process");

const MAX_OUTPUT_BYTES = 8 * 1024 * 1024;
const DEFAULT_IDLE_MS = 5 * 60 * 1000;
const WORKER_SOURCE = String.raw`
import contextlib, io, json, sys, traceback

class LimitedWriter(io.StringIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit
        self.size = 0
    def write(self, value):
        text = str(value)
        remaining = self.limit - self.size
        if remaining <= 0:
            return len(text)
        chunk = text[:remaining]
        self.size += len(chunk.encode("utf-8", "replace"))
        return super().write(chunk)

print(json.dumps({"ready": True}), flush=True)
for line in sys.stdin:
    try:
        request = json.loads(line)
        request_id = request.get("id")
        original_stdin = sys.stdin
        output = LimitedWriter(${MAX_OUTPUT_BYTES})
        try:
            sys.stdin = io.StringIO(str(request.get("input") or ""))
            scope = {"__name__": "__msbt_worker__"}
            with contextlib.redirect_stdout(output):
                exec(str(request.get("code") or ""), scope, scope)
            response = {"id": request_id, "ok": True, "stdout": output.getvalue()}
        except Exception:
            response = {"id": request_id, "ok": False, "error": traceback.format_exc(limit=12)}
        finally:
            sys.stdin = original_stdin
    except Exception:
        response = {"id": None, "ok": False, "error": traceback.format_exc(limit=12)}
    print(json.dumps(response, ensure_ascii=False), flush=True)
`;

class PersistentPythonWorker {
  constructor({ candidates, cwd, pythonPath, idleMs = DEFAULT_IDLE_MS, killTree = null }) {
    this.candidates = Array.from(new Set((candidates || []).filter(Boolean)));
    this.cwd = cwd;
    this.pythonPath = pythonPath;
    this.idleMs = idleMs;
    this.killTree = killTree;
    this.child = null;
    this.queue = [];
    this.current = null;
    this.nextId = 1;
    this.stdoutBuffer = "";
    this.stderrBuffer = "";
    this.startPromise = null;
    this.idleTimer = null;
  }

  run(code, input = "", timeoutMs = 15000) {
    if (this.queue.length >= 100) return Promise.reject(new Error("Python helper queue is full."));
    return new Promise((resolve, reject) => {
      this.queue.push({ id: this.nextId++, code, input, timeoutMs, resolve, reject });
      void this._drain();
    });
  }

  async _start() {
    if (this.child && this.child.exitCode === null && !this.child.killed) return;
    if (this.startPromise) return this.startPromise;
    this.startPromise = this._startCandidates().finally(() => {
      this.startPromise = null;
    });
    return this.startPromise;
  }

  async _startCandidates() {
    const errors = [];
    for (const executable of this.candidates) {
      try {
        await this._spawn(executable);
        return;
      } catch (error) {
        errors.push(`${executable}: ${error.message || error}`);
      }
    }
    throw new Error(errors.join("\n") || "No Python helper executable is available.");
  }

  _spawn(executable) {
    return new Promise((resolve, reject) => {
      const source = [
        "import sys",
        `sys.path.insert(0, ${JSON.stringify(this.pythonPath)})`,
        WORKER_SOURCE
      ].join("\n");
      const args = executable === "py" ? ["-3", "-u", "-c", source] : ["-u", "-c", source];
      const child = spawn(executable, args, {
        cwd: this.cwd,
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true
      });
      this.child = child;
      this.stdoutBuffer = "";
      this.stderrBuffer = "";
      let ready = false;
      const timer = setTimeout(() => fail(new Error(`Timed out starting Python worker. ${this.stderrBuffer}`.trim())), 6000);
      const fail = (error) => {
        clearTimeout(timer);
        if (this.child === child) this.child = null;
        this._killChild(child);
        reject(error);
      };
      child.stdout.on("data", (chunk) => {
        this.stdoutBuffer += chunk.toString();
        if (Buffer.byteLength(this.stdoutBuffer) > MAX_OUTPUT_BYTES + 1024 * 1024) {
          this._failWorker(new Error("Python worker stdout exceeded its 8MB cap."));
          return;
        }
        let newline;
        while ((newline = this.stdoutBuffer.indexOf("\n")) >= 0) {
          const line = this.stdoutBuffer.slice(0, newline).trim();
          this.stdoutBuffer = this.stdoutBuffer.slice(newline + 1);
          if (!line) continue;
          let message;
          try {
            message = JSON.parse(line);
          } catch {
            this._failWorker(new Error("Python worker returned invalid framed JSON."));
            return;
          }
          if (!ready && message.ready) {
            ready = true;
            clearTimeout(timer);
            resolve();
          } else {
            this._handleMessage(message);
          }
        }
      });
      child.stderr.on("data", (chunk) => {
        this.stderrBuffer = (this.stderrBuffer + chunk.toString()).slice(-MAX_OUTPUT_BYTES);
      });
      child.on("error", (error) => {
        if (!ready) fail(error);
        else this._failWorker(error);
      });
      child.on("exit", (code, signal) => {
        if (!ready) fail(new Error(`Python worker exited (${code ?? signal ?? "unknown"}).`));
        else if (this.child === child) this._failWorker(new Error(`Python worker exited (${code ?? signal ?? "unknown"}).`));
      });
    });
  }

  async _drain() {
    if (this.current || !this.queue.length) return;
    try {
      await this._start();
    } catch (error) {
      const queued = this.queue.shift();
      if (queued) queued.reject(error);
      void this._drain();
      return;
    }
    const request = this.queue.shift();
    if (!request || !this.child) return;
    this.current = request;
    request.timer = setTimeout(() => {
      this._failWorker(new Error(`Timed out running persistent Python helper after ${request.timeoutMs}ms.`));
    }, request.timeoutMs);
    try {
      this.child.stdin.write(`${JSON.stringify({ id: request.id, code: request.code, input: String(request.input || "") })}\n`);
    } catch (error) {
      this._failWorker(error);
    }
  }

  _handleMessage(message) {
    const request = this.current;
    if (!request || message.id !== request.id) return;
    clearTimeout(request.timer);
    this.current = null;
    if (message.ok) request.resolve(String(message.stdout || "").trim());
    else request.reject(new Error(String(message.error || "Python worker request failed.")));
    this._scheduleIdleStop();
    void this._drain();
  }

  _failWorker(error) {
    const child = this.child;
    this.child = null;
    if (child) this._killChild(child);
    if (this.current) {
      clearTimeout(this.current.timer);
      this.current.reject(error);
      this.current = null;
    }
    void this._drain();
  }

  _scheduleIdleStop() {
    if (this.idleTimer) clearTimeout(this.idleTimer);
    this.idleTimer = setTimeout(() => {
      if (!this.current && !this.queue.length) this.stop();
    }, this.idleMs);
  }

  _killChild(child) {
    if (!child || child.exitCode !== null) return;
    if (this.killTree) this.killTree(child.pid);
    else child.kill();
  }

  stop() {
    if (this.idleTimer) clearTimeout(this.idleTimer);
    this.idleTimer = null;
    const child = this.child;
    this.child = null;
    if (child) this._killChild(child);
  }
}

module.exports = { MAX_OUTPUT_BYTES, PersistentPythonWorker };
