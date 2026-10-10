/* Preparing an AFK list never starts a lobby or sends an item. */
(() => {
  const byId = id => document.getElementById(id);
  function review(guaranteed = false) {
    if (window.MsbtWorkspace?.enabled) window.MsbtWorkspace.open("boosting", "afk");
    else switchTab("boosting");
    byId("afkLootDetails").open = true;
    const target = byId(guaranteed ? "afkGuaranteedCodes" : "afkCodes");
    target.scrollIntoView({block:"center"}); target.focus({preventScroll:true});
  }
  function strip(name, anchor, read, existing = []) {
    if (!anchor) return;
    const box = document.createElement("section"); box.className = "afk-item-handoff"; box.dataset.afkSource = name;
    const heading = document.createElement("strong"); heading.textContent = "Prepare AFK items";
    const help = document.createElement("p"); help.textContent = name === "serials" || name === "converter"
      ? "Use one encoded @U serial per line. Adds to your saved setup; review it before starting AFK."
      : name === "bookmarks" ? "Select items here, then add them to your AFK setup. For a folder, use Select All in that folder first."
      : "Select items here, then add them to your AFK setup. Review the list before starting AFK.";
    const buttons = document.createElement("div"); buttons.className = "button-row wrap";
    const status = document.createElement("p"); status.className = "muted-line"; status.setAttribute("role", "status");
    let lastGuaranteed = false;
    [false, true].forEach((guaranteed, index) => {
      const button = existing[index] || document.createElement("button"); button.type = "button";
      button.textContent = guaranteed ? "Add to guaranteed items" : "Add to AFK loot pool";
      button.dataset.afkHandoff = guaranteed ? "guaranteed" : "pool";
      if (!existing[index]) button.addEventListener("click", () => {
        const rows = read();
        if (!rows.length) { status.textContent = "Select items or enter serials first. Nothing added."; return; }
        // Validate the entire selection before appending, preserving case, order and duplicates.
        const codes = rows.flatMap(row => String(row ?? "").split(/\r?\n/).map(s => s.trim()).filter(Boolean));
        if (rows.some(row => !String(row ?? "").trim()) || !codes.length || codes.some(code => serialValidationMessage(code))) {
          status.textContent = "One or more entries are not encoded @U serials. Nothing added. Convert decoded text in Serial Converter first."; return;
        }
        const result = window.msbtAfkAppendLoot(codes, guaranteed);
        status.textContent = result.message;
        if (result.ok) lastGuaranteed = guaranteed;
      });
      else button.addEventListener("click", () => { status.textContent = byId("bl4Status").textContent; lastGuaranteed = guaranteed; });
      buttons.append(button);
    });
    const show = document.createElement("button"); show.type = "button"; show.textContent = "Review AFK list";
    show.dataset.afkHandoff = "review"; show.addEventListener("click", () => review(lastGuaranteed)); buttons.append(show);
    box.append(heading, help, buttons, status); anchor.after(box);
  }
  strip("catalog", byId("bl4Status"), () => [], [byId("bl4AddToAfkBtn"), byId("bl4AddGuaranteedAfkBtn")]);
  byId("bl4AddThisToAfkBtn").textContent = "Add this to AFK loot pool";
  strip("bookmarks", byId("savedSendBtn"), () => savedDeliveryEntries().map(row => row.serial));
  strip("inventory", document.querySelector(".inv-count-row"), () => invSelectedEntries().map(row => row.serial));
  strip("serials", byId("boostSerialText"), () => [byId("boostSerialText").value]);
  strip("converter", byId("serialToolsSerialized").closest("label") || byId("serialToolsSerialized"), () => [byId("serialToolsSerialized").value]);
})();
