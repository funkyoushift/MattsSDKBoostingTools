import test from "node:test";
import assert from "node:assert/strict";
import worker from "./worker.js";

function env() {
  const stored = [];
  return {stored, UPLOAD_RATE: {limit: async () => ({success: true})},
    REPORTS: {list: async () => ({objects: [], truncated: false}), put: async (key, value) => stored.push({key, value})}};
}
const base = {version: 1, appVersion: "2.39.4", kind: "command_failure", occurredAt: new Date().toISOString(), action: "test", message: "failed", files: []};
function request(body) { return new Request("https://reports.example/v1/reports", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)}); }

test("accepts bounded failure report into private storage", async () => {
  const e = env();
  const result = await worker.fetch(request(base), e);
  assert.equal(result.status, 202);
  assert.equal(e.stored.length, 1);
  assert.deepEqual(JSON.parse(e.stored[0].value), base);
});

test("rejects arbitrary files and oversize text", async () => {
  const e = env();
  const result = await worker.fetch(request({...base, files: [{name: "save.sav", kind: "text", text: "bad"}]}), e);
  assert.equal(result.status, 400);
  assert.equal(e.stored.length, 0);
});

test("rate limit stops upload", async () => {
  const e = env(); e.UPLOAD_RATE.limit = async () => ({success: false});
  assert.equal((await worker.fetch(request(base), e)).status, 429);
  assert.equal(e.stored.length, 0);
});

test("public endpoint cannot read stored reports", async () => {
  const e = env();
  assert.equal((await worker.fetch(new Request("https://reports.example/v1/reports"), e)).status, 404);
  assert.equal(e.stored.length, 0);
});
