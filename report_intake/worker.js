const MAX_BODY = 28 * 1024 * 1024;
const MAX_DAILY_BYTES = 256 * 1024 * 1024;
const ALLOWED_FILES = new Map([
  ["recent-sdk.log", "text"],
  ["recent-game.log", "text"],
  ["CrashContext.runtime-xml", "text"],
  ["UEMinidump.dmp", "binary"]
]);

async function boundedBody(request) {
  const declared = Number(request.headers.get("content-length"));
  if (declared > MAX_BODY) throw new RangeError("Report too large");
  if (!request.body) throw new TypeError("Missing report");
  const reader = request.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > MAX_BODY) throw new RangeError("Report too large");
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const body = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder().decode(body));
}

function validReport(report) {
  if (!report || report.version !== 1 || !["command_failure", "desktop_failure", "game_crash"].includes(report.kind)) return false;
  if (typeof report.appVersion !== "string" || !/^\d+\.\d+\.\d+$/.test(report.appVersion)) return false;
  if (typeof report.occurredAt !== "string" || !Number.isFinite(Date.parse(report.occurredAt))) return false;
  if (report.action !== undefined && (typeof report.action !== "string" || report.action.length > 80)) return false;
  if (report.message !== undefined && (typeof report.message !== "string" || report.message.length > 8192)) return false;
  if (!Array.isArray(report.files) || report.files.length > 4) return false;
  for (const file of report.files) {
    if (!file || ALLOWED_FILES.get(file.name) !== file.kind) return false;
    if (file.kind === "text" && (typeof file.text !== "string" || file.text.length > 300000)) return false;
    if (file.kind === "binary" && (typeof file.base64 !== "string" || file.base64.length > 28 * 1024 * 1024 || !/^[A-Za-z0-9+/]*={0,2}$/.test(file.base64))) return false;
  }
  return true;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/v1/reports" || request.method !== "POST") return new Response("Not found", {status: 404});
    if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) return new Response("JSON required", {status: 415});
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const {success} = await env.UPLOAD_RATE.limit({key: ip});
    if (!success) return new Response("Rate limited", {status: 429});
    let report;
    try { report = await boundedBody(request); }
    catch (error) { return new Response(error instanceof RangeError ? "Report too large" : "Invalid report", {status: error instanceof RangeError ? 413 : 400}); }
    if (!validReport(report)) return new Response("Invalid report", {status: 400});
    const serialized = JSON.stringify(report);
    const reportBytes = new TextEncoder().encode(serialized).byteLength;
    const day = new Date().toISOString().slice(0, 10);
    const existing = await env.REPORTS.list({prefix: `${day}/`, limit: 1000});
    const used = existing.objects.reduce((sum, object) => sum + object.size, 0);
    if (existing.truncated || existing.objects.length >= 200 || used + reportBytes > MAX_DAILY_BYTES)
      return new Response("Report inbox is full today", {status: 503});
    const id = crypto.randomUUID();
    const key = `${day}/${id}.json`;
    await env.REPORTS.put(key, serialized, {httpMetadata: {contentType: "application/json"}});
    return Response.json({ok: true, id}, {status: 202, headers: {"Cache-Control": "no-store"}});
  }
};
