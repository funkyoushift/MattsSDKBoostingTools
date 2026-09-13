"use strict";
const fs = require("node:fs/promises");
const path = require("node:path");
const MAX_BYTES = 32 * 1024 * 1024;
const filename = "inventory_snapshot.json";

// Save serial identity and observed labels, not a stale copy of the calculator.
function normalizeSnapshot(raw) {
  if (!raw || raw.version !== 1 || !Number.isFinite(Date.parse(raw.saved_at)) ||
      !Array.isArray(raw.equipped) || !Array.isArray(raw.backpack)) throw new Error("Invalid inventory snapshot.");
  const entries = rows => {
    if (rows.length > 20000) throw new Error("Inventory snapshot has too many entries.");
    return rows.map(row => {
      if (!row || typeof row !== "object") throw new Error("Invalid inventory entry.");
      const entry = {};
      for (const key of ["serial","origin","slot","backpack_index","label","display_name","summary","card_name","meta_source","card_ok","level","item_type","category","rarity","manufacturer","element","damage_type"]) {
        const value = row[key];
        if (typeof value === "string" || typeof value === "boolean" || (typeof value === "number" && Number.isFinite(value))) entry[key] = value;
      }
      if (typeof entry.serial === "string" && entry.serial.length > 200000) throw new Error("Inventory serial is too long.");
      return entry;
    });
  };
  return {version:1,saved_at:new Date(raw.saved_at).toISOString(),reading:String(raw.reading || "Unknown player").slice(0,1000),
    truncated:Boolean(raw.truncated),equipped:entries(raw.equipped),backpack:entries(raw.backpack)};
}
async function loadSnapshot(directory) {
  try {
    const file = path.join(directory,filename);
    if ((await fs.stat(file)).size > MAX_BYTES) throw new Error("Inventory snapshot is too large.");
    return {ok:true,snapshot:normalizeSnapshot(JSON.parse(await fs.readFile(file,"utf8")))};
  } catch (error) {
    if (error.code === "ENOENT") return {ok:true,snapshot:null};
    return {ok:false,message:error.message};
  }
}
let writes = Promise.resolve();
function saveSnapshot(directory,raw) {
  const work = writes.then(async () => {
    const snapshot = normalizeSnapshot(raw), text = JSON.stringify(snapshot);
    if (Buffer.byteLength(text) > MAX_BYTES) throw new Error("Inventory snapshot is too large.");
    await fs.mkdir(directory,{recursive:true});
    const file = path.join(directory,filename), temporary = file + ".tmp";
    await fs.writeFile(temporary,text,"utf8");
    await fs.rename(temporary,file);
    return {ok:true};
  });
  writes = work.catch(()=>{});
  return work.catch(error=>({ok:false,message:error.message}));
}
module.exports = {loadSnapshot,saveSnapshot,normalizeSnapshot};
