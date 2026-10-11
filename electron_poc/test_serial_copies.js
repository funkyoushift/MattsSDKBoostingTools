const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(require("node:path").join(__dirname, "renderer.js"), "utf8");
function extract(name) {
  const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, "m"));
  assert.ok(start >= 0, name);
  const end = source.indexOf("\n}", start);
  return source.slice(start, end + 2);
}
const sent = [];
const context = vm.createContext({
  appendActivity() {},
  els: { boostSerialText: "", boostSerialCopies: 1, boostSerialOverride: false, boostSerialLevel: 50 },
  state: { gameParameters: { item_level_cap: 50 } },
  getValue: value => value,
  getInt: (value, min, max, fallback) => Number(value) || fallback,
  boolFromSelect: Boolean,
  ensureLiveSdkReady: async () => ({ ok: true }),
  ensureSelectedTarget: async () => true,
  serialActionByMode: mode => mode,
  runAction: async (action, payload) => { sent.push({ action, payload }); return { ok: true }; },
  startSerialDeliveryProgressWatch() {},
});
vm.runInContext(["serialDeliveryRows", "expandSerialTextCopies", "quickMenuSerialPayload", "sendSerialPayload"].map(extract).join("\n"), context);
(async () => {
  for (const code of ["@UAbC`x@Uyz", "1, 2, 3, 50 | 4, 5", "1 2 3 50 4 5", "`@UAbCd`"]) {
    for (const count of [1, 5, 10]) {
      const expanded = context.expandSerialTextCopies(code, count);
      assert.equal(expanded.text, Array(count).fill(code).join("\n"));
      assert.equal(expanded.totalCount, count);
      context.els.boostSerialText = code;
      context.els.boostSerialCopies = count;
      assert.equal(context.quickMenuSerialPayload().serial_text, expanded.text);
      for (const mode of ["self", "selected", "all", "others"]) {
        await context.sendSerialPayload(mode, code, true, 50, null, count);
        assert.equal(sent.at(-1).payload.serial_text, expanded.text);
        assert.equal(sent.at(-1).payload.serial_level, 50);
      }
    }
  }
  const repeated = "@UAbC\n@UAbC\n@Uabc";
  assert.equal(context.expandSerialTextCopies(repeated, 1).text, repeated);
  assert.equal(context.expandSerialTextCopies(repeated, 2).text, "@UAbC\n@UAbC\n@UAbC\n@UAbC\n@Uabc\n@Uabc");
  assert.equal(context.expandSerialTextCopies("@Uone @Utwo", 5).totalCount, 10);
  assert.equal(context.expandSerialTextCopies("\n \n", 10).totalCount, 0);
  assert.equal(context.expandSerialTextCopies("@Uone", 100).totalCount, 50);
  assert.equal(context.expandSerialTextCopies("@Uone", 0).totalCount, 1);
  console.log("Serial quantity regression checks passed (desktop payloads, Quick Menu, readable codes, duplicates).");
})().catch(error => { console.error(error); process.exitCode = 1; });
