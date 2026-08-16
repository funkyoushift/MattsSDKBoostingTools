"use strict";

const assert = require("assert");
const {
  pollDelay,
  serialDeliveryFingerprint,
  stableFingerprint
} = require("./poll_coordinator");

assert.strictEqual(pollDelay({ hidden: true, active: true }), 8000);
assert.strictEqual(pollDelay({ active: true }), 1250);
assert.strictEqual(pollDelay({ active: false }), 4000);

assert.strictEqual(
  stableFingerprint({ b: 2, a: [{ z: 1, y: 0 }] }),
  stableFingerprint({ a: [{ y: 0, z: 1 }], b: 2 })
);
assert.notStrictEqual(
  stableFingerprint([{ index: 0, name: "Host" }]),
  stableFingerprint([{ index: 1, name: "Guest" }])
);

assert.strictEqual(
  serialDeliveryFingerprint({ active: true, current: 1, total: 3, ignored: Date.now() }),
  serialDeliveryFingerprint({ total: 3, current: 1, active: true })
);
assert.notStrictEqual(
  serialDeliveryFingerprint({ active: true, current: 1, total: 3 }),
  serialDeliveryFingerprint({ active: true, current: 2, total: 3 })
);

console.log("poll coordinator tests passed");
