/**
 * Minimal LAN gateway for MSBT Mobile Controller closed beta.
 * Proxies /status and /action to the local SDK bridge (127.0.0.1:49774)
 * so phones on the same Wi-Fi can fire live actions without opening the
 * in-game bridge beyond localhost.
 */
const http = require("http");
const https = require("https");
const os = require("os");
const crypto = require("crypto");
const { URL } = require("url");

const DEFAULT_PORT = 49775;
const DEFAULT_BRIDGE = "http://127.0.0.1:49774";
const PAIRING_HEADER = "x-msbt-pairing-code";

function listLanAddresses() {
  const interfaces = os.networkInterfaces();
  const addresses = [];
  for (const entries of Object.values(interfaces)) {
    if (!entries) continue;
    for (const entry of entries) {
      if (!entry || entry.internal) continue;
      if (entry.family !== "IPv4" && entry.family !== 4) continue;
      addresses.push(entry.address);
    }
  }
  return [...new Set(addresses)];
}

function generatePairingCode() {
  return String(crypto.randomInt(100000, 1000000));
}

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, X-MSBT-Pairing-Code",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Cache-Control": "no-store"
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > 2 * 1024 * 1024) {
        reject(new Error("Request body too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function proxyToBridge(bridgeBase, method, route, bodyBuffer, timeoutMs) {
  return new Promise((resolve) => {
    let target;
    try {
      target = new URL(route, bridgeBase.endsWith("/") ? bridgeBase : `${bridgeBase}/`);
    } catch (error) {
      resolve({
        statusCode: 500,
        headers: { "content-type": "application/json" },
        body: Buffer.from(JSON.stringify({ ok: false, message: String(error && error.message ? error.message : error) }))
      });
      return;
    }

    const lib = target.protocol === "https:" ? https : http;
    const headers = {
      Accept: "application/json",
      "Content-Type": "application/json"
    };
    if (bodyBuffer && bodyBuffer.length) {
      headers["Content-Length"] = bodyBuffer.length;
    }

    const request = lib.request(
      {
        protocol: target.protocol,
        hostname: target.hostname,
        port: target.port,
        path: `${target.pathname}${target.search}`,
        method,
        headers,
        timeout: timeoutMs
      },
      (upstream) => {
        const chunks = [];
        upstream.on("data", (chunk) => chunks.push(chunk));
        upstream.on("end", () => {
          resolve({
            statusCode: upstream.statusCode || 502,
            headers: upstream.headers || {},
            body: Buffer.concat(chunks)
          });
        });
      }
    );

    request.on("timeout", () => {
      request.destroy(new Error("Bridge proxy timeout"));
    });
    request.on("error", (error) => {
      resolve({
        statusCode: 502,
        headers: { "content-type": "application/json" },
        body: Buffer.from(
          JSON.stringify({
            ok: false,
            message: `SDK bridge unreachable at ${bridgeBase}. Launch Borderlands 4 with MSBT loaded. (${error && error.message ? error.message : error})`
          })
        )
      });
    });

    if (bodyBuffer && bodyBuffer.length) request.write(bodyBuffer);
    request.end();
  });
}

function createMobileGateway(options = {}) {
  const port = Number(options.port) > 0 ? Number(options.port) : DEFAULT_PORT;
  const bridgeBase = String(options.bridgeBase || DEFAULT_BRIDGE).replace(/\/$/, "");
  let pairingCode = String(options.pairingCode || generatePairingCode()).trim() || generatePairingCode();
  let server = null;
  let lastError = "";
  let startedAt = null;

  function info() {
    return {
      ok: true,
      service: "msbt-mobile-gateway",
      enabled: Boolean(server && server.listening),
      host: "0.0.0.0",
      port,
      pairingCode,
      lanAddresses: listLanAddresses(),
      bridgeBase,
      startedAt,
      lastError: lastError || ""
    };
  }

  function setPairingCode(nextCode) {
    const cleaned = String(nextCode || "").trim();
    pairingCode = cleaned || generatePairingCode();
    return pairingCode;
  }

  function rotatePairingCode() {
    pairingCode = generatePairingCode();
    return pairingCode;
  }

  function authorized(req) {
    const provided = String(req.headers[PAIRING_HEADER] || "").trim();
    return provided && provided === pairingCode;
  }

  async function handle(req, res) {
    const method = String(req.method || "GET").toUpperCase();
    const requestUrl = new URL(req.url || "/", `http://${req.headers.host || "127.0.0.1"}`);
    const pathname = requestUrl.pathname || "/";

    if (method === "OPTIONS") {
      sendJson(res, 200, { ok: true });
      return;
    }

    // Unauthenticated discovery for testers confirming the gateway is reachable.
    if (method === "GET" && (pathname === "/mobile/ping" || pathname === "/ping")) {
      sendJson(res, 200, {
        ok: true,
        service: "msbt-mobile-gateway",
        port,
        lanAddresses: listLanAddresses()
      });
      return;
    }

    if (method === "GET" && pathname === "/mobile/info") {
      if (!authorized(req)) {
        sendJson(res, 401, { ok: false, message: "Invalid or missing pairing code." });
        return;
      }
      sendJson(res, 200, info());
      return;
    }

    if (method === "GET" && pathname === "/mobile/bookmarks") {
      if (!authorized(req)) {
        sendJson(res, 401, { ok: false, message: "Invalid or missing pairing code." });
        return;
      }
      try {
        const bookmarks =
          typeof options.getSerialBookmarks === "function" ? await options.getSerialBookmarks() : [];
        sendJson(res, 200, {
          ok: true,
          bookmarks: Array.isArray(bookmarks) ? bookmarks : [],
          count: Array.isArray(bookmarks) ? bookmarks.length : 0
        });
      } catch (error) {
        sendJson(res, 500, {
          ok: false,
          message: String(error && error.message ? error.message : error)
        });
      }
      return;
    }

    if (!authorized(req)) {
      sendJson(res, 401, { ok: false, message: "Invalid or missing pairing code." });
      return;
    }

    const allowedGet = pathname === "/status" || pathname === "/quick_menu" || pathname.startsWith("/status?") || pathname.startsWith("/quick_menu?");
    const allowedPost = pathname === "/action" || pathname.startsWith("/action?");
    if (method === "GET" && allowedGet) {
      const upstream = await proxyToBridge(bridgeBase, "GET", pathname + requestUrl.search, null, 10000);
      res.writeHead(upstream.statusCode, {
        "Content-Type": upstream.headers["content-type"] || "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, X-MSBT-Pairing-Code",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Cache-Control": "no-store"
      });
      res.end(upstream.body);
      return;
    }

    if (method === "POST" && allowedPost) {
      let body;
      try {
        body = await readBody(req);
      } catch (error) {
        sendJson(res, 413, { ok: false, message: String(error && error.message ? error.message : error) });
        return;
      }
      const upstream = await proxyToBridge(bridgeBase, "POST", pathname + requestUrl.search, body, 45000);
      res.writeHead(upstream.statusCode, {
        "Content-Type": upstream.headers["content-type"] || "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, X-MSBT-Pairing-Code",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Cache-Control": "no-store"
      });
      res.end(upstream.body);
      return;
    }

    sendJson(res, 404, { ok: false, message: "Not found" });
  }

  function start() {
    if (server) {
      return Promise.resolve(info());
    }
    return new Promise((resolve, reject) => {
      const next = http.createServer((req, res) => {
        handle(req, res).catch((error) => {
          lastError = String(error && error.message ? error.message : error);
          sendJson(res, 500, { ok: false, message: lastError });
        });
      });
      next.on("error", (error) => {
        lastError = String(error && error.message ? error.message : error);
        server = null;
        reject(error);
      });
      next.listen(port, "0.0.0.0", () => {
        server = next;
        startedAt = new Date().toISOString();
        lastError = "";
        resolve(info());
      });
    });
  }

  function stop() {
    return new Promise((resolve) => {
      if (!server) {
        resolve(info());
        return;
      }
      const current = server;
      server = null;
      current.close(() => {
        startedAt = null;
        resolve(info());
      });
    });
  }

  return {
    info,
    start,
    stop,
    setPairingCode,
    rotatePairingCode,
    listLanAddresses
  };
}

module.exports = {
  DEFAULT_PORT,
  DEFAULT_BRIDGE,
  PAIRING_HEADER,
  createMobileGateway,
  listLanAddresses,
  generatePairingCode
};
