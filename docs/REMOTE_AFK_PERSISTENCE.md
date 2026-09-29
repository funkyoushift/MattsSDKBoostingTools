# Remote AFK persistence and reserved-port repair

Shipping in desktop/SDK v2.21.0 and Android v1.4.3 (30), following Martin's successful local review and explicit release approval. Older published assets remain unchanged.

## Behavior

- Remote AFK restores the existing encrypted pairing at desktop startup. Network failure keeps it enabled and retries; reconnects register the same credentials, and the seven-day relay lease is renewed every six hours. No relay deployment is required.
- While remote access is enabled, closing the desktop window hides it in the tray. A dedicated Windows sign-in entry restores it after login, and a sleep blocker prevents automatic suspension. Explicit Quit, shutdown, lost power/internet, and a stopped game still make game control unavailable. This does not launch the game or resume a stopped lobby automatically.
- Android retries read-only status after connection failure and on foreground/network return. Manual Disconnect stops retries. Actions are never automatically repeated after an uncertain response.
- SDK bridge tries 49774, 27874, 27875, then 27876, logs every bind failure and the selected endpoint, and advertises its current instance in LocalAppData/MSBT/bridge-endpoint.json. Desktop verifies identity before using the endpoint and before every action; commands carry the instance identifier. Legacy default-port bridges remain supported through their original status identity.
- Desktop LAN gateway tries 49775, 27877, then 27878. Desktop, gateway, encrypted remote control, direct-phone connection discovery, and SHiFT AFK automation use the fallback endpoints. No Windows excluded-port ranges are modified.
- The bundled SHiFT PAK changes only the AFK link; all 192 extracted payloads round-trip, and its manifest hash is updated. The source-only refresh tool never writes to a game installation.
- Packaging rejects junction-backed node_modules and checks dependencies, QR generation, renderer assets, and source/resource hashes inside the actual packaged app.

## Compatibility

The rebrand retains Mattmab credit. Repository slug, app IDs, executable, profile/settings names, SDK filename, bridge commands, updater target, website URLs, signing identity, and release asset names remain legacy-compatible. Remote QR v3 credentials are reused; disabling remote access revokes the local pairing and a later enable creates new credentials.

## Validation

Python syntax and bridge lifecycle/Quick Menu regression checks; real sockets for denied-port fallback and stale-instance rejection; unrelated-server/action routing and LAN fallback tests; remote restore, offline enable, renewal, reconnect, revoke and shutdown-race tests; phone retry/cancellation and desktop tray/sleep/login tests; SHiFT link tests; desktop checks, settings restart and mobile parity/UI checks. Live hosted relay tested only against a mock game bridge for encryption, allowlist, replay rejection, auth and revocation.

Martin confirmed the installed candidate works before authorizing publication. The local review checklist covered the updated SDK and PAK in the active Steam game installation after a normal game restart, real phone control over cellular, window-close/reopen and PC sign-in recovery, and a real guest join/rejoin. Offline tests and a mocked hosted relay do not prove those live-game behaviors. Do not launch the retained Epic installation.
