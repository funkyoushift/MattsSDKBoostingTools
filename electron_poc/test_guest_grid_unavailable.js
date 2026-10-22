const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const html = fs.readFileSync(path.join(__dirname, "renderer.html"), "utf8");
for (const label of ["Dump Guest Grid (dev)", "Fill Guest Grid (dev)"]) {
  const button = html.match(/<button\b[^>]*>[^<]*Guest Grid \(dev\)<\/button>/g)
    .find(value => value.includes(label));
  assert.ok(button, label);
  assert.match(button, /\bdisabled\b/);
  assert.match(button, /aria-describedby="guestGridUnavailable"/);
  assert.doesNotMatch(button, /data-action=/);
}
assert.match(html, /id="guestGridUnavailable"[^>]*>[^<]*no handler/);
console.log("PASS unavailable Guest Grid probes are disabled and explained");
