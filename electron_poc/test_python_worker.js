"use strict";

const assert = require("assert");
const { PersistentPythonWorker } = require("./python_worker");

async function main() {
  const worker = new PersistentPythonWorker({
    candidates: [process.env.MSBT_PYTHON || "python"],
    cwd: __dirname,
    pythonPath: __dirname,
    idleMs: 10000
  });
  try {
    const output = await worker.run(
      "import json, sys\nprint(json.dumps({'ok': True, 'value': sys.stdin.read()}))",
      "phase4",
      5000
    );
    assert.deepStrictEqual(JSON.parse(output), { ok: true, value: "phase4" });
    console.log("python worker smoke test passed");
  } finally {
    worker.stop();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
