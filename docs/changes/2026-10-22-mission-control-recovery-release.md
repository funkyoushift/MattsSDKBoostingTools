# Mission-control recovery patch — 2026-10-22

An October 17 save-backed replay journal remained failed and open after its game process ended. In installed v2.39.3 this silently disabled all desktop mission actions, although the current bridge and live mission previews were healthy. Using the existing Stop setup action closed that old journal while preserving its verified backup and the current lobby; no save or mission was changed.

The isolated `codex/mission-lock-2394` release branch adds a persistent explanation and Stop control outside the mission subviews. A replay lock transition recomputes mission and Full Game availability immediately. The stop remains explicit and retains the backup; no automatic restore or live completion occurs. The SDK game logic and Android code are unchanged apart from version metadata.

The same branch includes the separately verified desktop atomic-writer cleanup from the incident repair. After an owned temporary file has been created, a failed write, sync, or rename closes and removes that exact file without hiding the original error. A pre-existing file is never claimed or removed. Five injected failure cases and the full 55-case replay service suite pass. This does not prove the customers' save errors were caused by the leak.

The focused Electron stale-lock, mission-view, Full Game panel and syntax checks passed before packaging. Packaged, installed, and publication evidence is recorded separately in `docs/releases/VERIFICATION_v2.39.4.txt`. This patch does not prove the reported customer crash/save cause, complete mission overhaul, guest persistence, or 100% coverage. The experimental mission branch remains separate for later work.
