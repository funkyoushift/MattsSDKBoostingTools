# Beta test checklist — MSBT Mobile Controller

Check boxes as you go. Test **portrait** and **landscape** where it matters. Prefer **full-screen** screenshots.

**Your info**

- Phone make/model: _______________
- Android version: _______________
- App version (More → About): _______________
- Desktop MSBT version (if known): _______________

---

## A. Install / launch

- [ ] APK installs (or updates over prior beta) without error
- [ ] App opens to Home without crash
- [ ] About shows current beta version
- [ ] Bottom nav: Home · Boost · Codes · QM · Control · Spawn · More (scroll nav if needed)

## B. Connection (live)

- [ ] Desktop **Mobile Gateway tab** shows a QR
- [ ] Phone **Scan QR to pair** fills address/port/code and connects
- [ ] Manual setup still works (address / `49775` / pairing code)
- [ ] Reopen app — saved setup still there
- [ ] Badge **ONLINE** after connect
- [ ] Game bridge shows online while in-world
- [ ] Wrong pairing code fails clearly; saved setup not wiped
- [ ] **Disconnect** keeps saved setup
- [ ] Camera permission denied → clear message; manual still works

## C. Home / navigation

- [ ] Status text readable, not clipped
- [ ] Bottom nav clears Android gesture bar
- [ ] Rotate phone — layout still usable
- [ ] Screenshot: Home connected (or clear offline state)

## D. Boost (paired + in-game)

- [ ] Target player list populates after Connect in-world
- [ ] **MAX CASH** (or similar) succeeds
- [ ] Currency / Set Level works
- [ ] Serial Validate → Confirm → Send Selected works
- [ ] Send Non-Host button fully visible (not cut off)
- [ ] UVH buttons respond (status/cancel if you run a tier)
- [ ] Offline: live buttons disabled or refuse clearly

## E. BL4 Codes (offline OK)

- [ ] Catalog loads with **nonzero** count (thousands expected)
- [ ] Status shows GZO / Lootlemon / MSBT counts (or explicit error)
- [ ] Listing filter: Modded / Legit / Lootlemon
- [ ] Creator / search / Select all filtered / Clear work
- [ ] Multi-select + delivery Send works while paired
- [ ] Wi‑Fi off + relaunch: bundled catalog still loads
- [ ] Screenshot: Codes with multi-select

## F. Quick Menu (QM tab)

- [ ] QM tab opens; pages/slots visible
- [ ] **Pull From PC** loads live F7 layout (game + gateway up)
- [ ] Tap an assigned slot fires while connected
- [ ] Offline edits persist after relaunch
- [ ] Screenshot: QM page

## G. Control → Inventory

- [ ] Refresh Inventory / Equipped / Backpack while paired
- [ ] List scrolls; Select All / Clear work
- [ ] Collapse hides the panel
- [ ] Use in Boost / Bookmark / Send Selected work on selection

## H. Control → Bookmarks

- [ ] **Pull From MSBT** returns desktop bookmarks (not zero if PC has any)
- [ ] List scrolls; Select All / Clear / Collapse work
- [ ] Save Local / Delete / Use in Boost / Send Selected work

## I. Control → Map Travel

- [ ] Maps list loads and scrolls
- [ ] Selecting a map filters stations for that map
- [ ] **Show all travel stations** works
- [ ] Travel to Map / Travel to Station fire while paired

## J. Control → Movement

- [ ] Panel scrolls; sections fold; Collapse works
- [ ] Select All marks actions; **Run Selected Actions** works (or single-tap fires)
- [ ] Apply to Target / presets / infinite jump / helpers respond when paired

## K. Control → Item Pools

- [ ] Pool list loads / search works
- [ ] Spawn Selected Pool works while paired

## L. Spawn (Dev Spawner)

- [ ] Check **I understand the risk**, then **Enable Dev Spawner This Session**
- [ ] Button label becomes **Dev Spawner Enabled**; spawn actions unlock
- [ ] Actor browser loads / search / category / paging work
- [ ] Spawn Selected Actor works (expect experimental risk)
- [ ] Setup/Inspect + Advanced buttons respond
- [ ] Barrel Logo fields + Run respond
- [ ] Clear ASD Spawns available after heavy spawn tests

## M. More

- [ ] Activity Log shows recent actions
- [ ] Feedback template copy works
- [ ] About version matches installed beta

---

## Screenshots to send (minimum)

1. Home — connected  
2. Connection Settings — saved PC  
3. Boost — after a successful live action (or error)  
4. Codes — multi-select  
5. QM — one page  
6. Any clipped / broken screen (full-screen)

## Pass / fail notes

Write short notes for anything that failed (screen, steps, every time?).
