"use strict";

/**
 * Matt Editor must not share Mobile Gateway's port (49775). A collision
 * serves JSON on GET / and Chromium paints its Pretty-print viewer
 * instead of the editor UI.
 */
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { looksLikeEditorHtml } = require("./matt_editor_page");

const hostPy = fs.readFileSync(
  path.join(__dirname, "..", "external_app", "v22_parts_codes_fixed", "matt_editor_host.py"),
  "utf8"
);
const gatewayJs = fs.readFileSync(path.join(__dirname, "mobile_gateway.js"), "utf8");
const mainJs = fs.readFileSync(path.join(__dirname, "main.js"), "utf8");
const rendererHtml = fs.readFileSync(path.join(__dirname, "renderer.html"), "utf8");
const rendererJs = fs.readFileSync(path.join(__dirname, "renderer.js"), "utf8");
const styles = fs.readFileSync(path.join(__dirname, "styles.css"), "utf8");

assert.match(gatewayJs, /const DEFAULT_PORT = 49775/);
assert.match(hostPy, /MOBILE_GATEWAY_PORT = 49775/);
assert.match(hostPy, /PREFERRED_PORT = 49776/);
assert.match(hostPy, /allow_reuse_address = False/);
assert.match(hostPy, /refusing to bind Matt editor on Mobile Gateway port/);
assert.doesNotMatch(hostPy, /ThreadingHTTPServer\(\("127\.0\.0\.1", 49775\)/);

assert.match(mainJs, /looksLikeEditorHtml/);
assert.match(mainJs, /probeMattEditorUrl/);
assert.match(rendererHtml, /id="editorTabStatus"/);
assert.match(rendererHtml, /id="editorFrame"/);
assert.match(rendererJs, /function setEditorTabStatus/);
assert.match(styles, /\.tab-shell:has\(#tab-matt-editor\.active\)/);

assert.strictEqual(looksLikeEditorHtml('{"ok":true}', "application/json"), false);
assert.strictEqual(looksLikeEditorHtml("{", "text/plain"), false);
assert.strictEqual(
  looksLikeEditorHtml("<!DOCTYPE html><html><body>Matt</body></html>", "text/html"),
  true
);
assert.strictEqual(looksLikeEditorHtml("<html></html>", ""), true);

console.log("matt editor host port tests passed");
