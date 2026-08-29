/**
 * Shared checks so the Matt Editor iframe is never pointed at a JSON dump
 * (Chromium's Pretty-print viewer). Mobile Gateway on 49775 answers GET /
 * with application/json.
 */
"use strict";

function looksLikeEditorHtml(body, contentType) {
  const ct = String(contentType || "").toLowerCase();
  const text = String(body || "").replace(/^\uFEFF/, "").trimStart();
  if (ct.includes("json")) return false;
  if (text.startsWith("{") || text.startsWith("[")) return false;
  if (ct.includes("html")) return true;
  return text.startsWith("<");
}

module.exports = { looksLikeEditorHtml };
