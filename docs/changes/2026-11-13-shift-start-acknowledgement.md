# SHiFT repeated Start acknowledgement repair

A native Windows test of the unpublished 2.41.3 candidate sent rapid Stop/Start/Stop/Start commands. The final Start timed out after ten seconds although native acceptance stayed active. A separated Stop and Start worked.

The companion gives each desktop command a new ID. The JavaScript client marked that ID seen before invoking start(), whose active/pending guard returned without sending a request. The native command therefore received no acknowledgement. Replaying the same command ID was already covered by tests; a fresh Start ID while active was not.

`tools/afk_lobby/shift_background.js` confirms fresh Start commands using the existing page-owned session token. Same-process authorization, endpoint identity, lease ownership and Stop handling remain in force. The initial150ms rendering delay is explicitly retained: a Start arriving during it is confirmed by the original scheduled request rather than sending early. `test_shift_background.js` covers pending/active states, changed advertised nonce, rapid supersession during a heartbeat, subsequent Stop and the initial delay.

The new regression fails against the original implementation and passes the repair. JavaScript syntax/lifecycle checks and60 selected Python background/HTTP/routing/menu/startup tests pass. These are offline tests; they do not establish native repaired-artifact qualification. Exact commands and source hashes are retained in the local trial receipt.

The reviewed source archive BL4_ShiftAutomation_v4_4_SDK_BRIDGE_RESEARCHED.zip was located in Downloads and verified against pinned SHA2563e31ba6dfb91f014627df7cb9c453a34c8d13d2b49e1c6855bb8955f36ded440. Rebuilt PAK preserves192 entries; only dashboard_controller.js changes, with its pre-client prefix identical. Existing companion bytes are retained because this repair changes only the page client; a fresh companion build exhibited native.py newline-only drift and is not substituted.

Earlier Windows storage checks proved failed-write preservation/recovery and reviewed empty-list Save using task-owned data. Those unchanged-component results remain supporting evidence, not fabricated passes for new artifact hashes. Original settings absence and installed integration hashes were restored/verified after the trial; BL3 on5070Ti was untouched while BL4 used4090. The existing candidate packages/tag target the older source and must not be published as repaired artifacts. Rebuilt desktop package/native results remain pending; no version or tag is changed by this source repair.
