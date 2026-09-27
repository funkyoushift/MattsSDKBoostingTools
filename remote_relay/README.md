# MSBT remote AFK relay

The desktop initiates an outbound TLS WebSocket. The phone sends HTTPS requests through this Cloudflare Worker and Durable Object. There are no inbound router mappings or additional VPN programs. Desktop MSBT and the game must remain running.

The QR pairs a phone using independent 256-bit relay credentials and an AES-GCM key. The owner credential never leaves the desktop except as a TLS authorization header to the relay. Windows safeStorage encrypts saved desktop credentials. The relay stores the phone credential hash and routes encrypted envelopes; it does not receive the encryption key. Application logging is disabled. Pairing data on the phone uses its existing private WebView app storage; treat the QR as a secret.

Remote requests are restricted to AFK status, AFK start/stop, and SHiFT open/close. The desktop enforces this allowlist. Timestamps, unique request IDs and an in-memory replay cache reject stale/duplicate commands; commands are never automatically retried. Turning remote access off closes the desktop socket, revokes the relay pairing and deletes local credentials. Each new pairing gets a new room and keys. Quitting MSBT stops remote access; enable again after launching it. Idle registrations expire after seven days. A long-running session must be re-enabled after expiration.

The service limits request size, pending requests, authenticated room traffic and per-IP traffic. It cannot execute shell commands or forward arbitrary URLs. Hosting resources belong to the connected Cloudflare account. This is a separate service deployment, not a desktop or APK public release.

## Development

- `npm ci`
- `npx wrangler dev --local --port 8788`
- From electron_poc: set MSBT_TEST_RELAY to http://127.0.0.1:8788, then run `node test_remote_afk.js`. This creates a synthetic pairing, checks encrypted requests and revocation, and does not call the game.
- `npx wrangler types` and `npm run check` validate deployment configuration.
- Production worker: msbt-afk-relay, class AfkRoom, ROOMS binding, RATE binding, migration v1.
- Endpoint: https://msbt-afk-relay.screename53.workers.dev

## Phone testing

Use the locally built test APK. In desktop MSBT, open Mobile Gateway, enable Remote AFK and scan the private QR using the mobile app's existing Pair QR scanner. Turn phone Wi-Fi off and verify status/start/stop with a test lobby. Confirm revocation disconnects the phone. Never publish a QR screenshot or include pairing credentials in bug reports.
