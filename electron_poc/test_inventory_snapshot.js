"use strict";
const assert = require("node:assert/strict"), fs = require("node:fs/promises"), os = require("node:os"), path = require("node:path");
const {app,BrowserWindow} = require("electron");
const store = require("./inventory_snapshot_store");
app.on("window-all-closed",()=>{});
app.whenReady().then(async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(),"msbt-inventory-test-"));
  let win;
  try {
    const fixture = require("./fixtures/item_cards/mixed_order_user.json")[10];
    const raw = {version:1,saved_at:"2026-09-13T12:00:00Z",reading:"Reading: Original player",truncated:false,
      equipped:[],backpack:[{serial:fixture.serial,origin:"backpack",backpack_index:0,display_name:"Old guess",damage:999999},
        {serial:fixture.serial,origin:"backpack",backpack_index:1}]};
    assert.equal((await store.saveSnapshot(directory,raw)).ok,true);
    const saved = await store.loadSnapshot(directory);
    assert.equal(saved.snapshot.backpack.length,2,"identical serials at distinct positions survive");
    assert.equal(saved.snapshot.backpack[0].serial,fixture.serial,"case-sensitive serial survives exactly");
    assert.equal(saved.snapshot.backpack[0].damage,undefined,"do not freeze calculated numbers in the snapshot");
    assert.equal((await store.saveSnapshot(directory,{version:99})).ok,false);
    assert.deepEqual(await store.loadSnapshot(directory),saved,"invalid save preserves previous inventory");
    const card = require("./serial_card_resolve").loadResolver({sourceRoot:path.resolve(__dirname,"..")}).resolveFromHuman(fixture.human);
    win = new BrowserWindow({show:false,webPreferences:{partition:`inventory-snapshot-${process.pid}`,sandbox:true}});
    await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1"}});
    const result = await win.webContents.executeJavaScript(`(async()=>{
      window.MSBTNativeCard.enabled=false;
      const saved=${JSON.stringify(saved)}, card=${JSON.stringify(card)};
      let bridgeCalls=0, writes=0;
      window.msbt={loadInventorySnapshot:async()=>saved,saveInventorySnapshot:async()=>{writes++;return {ok:true};},
        serialCardResolve:async payload=>({ok:true,cards:payload.serials.map(serial=>({ok:true,serial,card}))}),
        bridgeRequest:async()=>{bridgeCalls++;throw new Error('BL4 closed');}};
      state.selectedTarget='1|Other player';
      await restoreInventorySnapshot();
      const restored={name:state.invBackpack[0]?.display_name,damage:state.invBackpack[0]?.damage,
        count:state.invBackpack.length,reading:els.invReading.textContent,target:state.selectedTarget,bridgeCalls};
      await refreshInventory();
      const afterFailure={count:state.invBackpack.length,reading:els.invReading.textContent,writes};
      let finish;
      window.msbt.loadInventorySnapshot=()=>new Promise(resolve=>{finish=resolve;});
      const pending=restoreInventorySnapshot();
      await refreshInventory();
      state.invBackpack=[{serial:'new-read'}];
      finish(saved);await pending;
      return {restored,afterFailure,raceSerial:state.invBackpack[0].serial};
    })()`);
    assert.equal(result.restored.count,2);assert.equal(result.restored.name,"Zealous Regulated Bubbles");
    assert.equal(result.restored.damage,541);assert.equal(result.restored.target,"1|Other player");
    assert.equal(result.restored.bridgeCalls,0);assert.match(result.restored.reading,/Saved inventory.*Original player/);
    assert.equal(result.afterFailure.count,2);assert.equal(result.afterFailure.writes,0);
    assert.match(result.afterFailure.reading,/Saved inventory.*Original player/);
    assert.equal(result.raceSerial,"new-read");
    console.log("PASS saved Inventory: disk roundtrip, duplicate identities, recalculated cards with no bridge, player label, failure preservation, restore/read race.");
  } finally {
    if(win)win.destroy();
    if(path.dirname(directory)!==path.resolve(os.tmpdir())||!path.basename(directory).startsWith("msbt-inventory-test-"))throw new Error("Unexpected test directory");
    await fs.rm(directory,{recursive:true,force:true});
  }
  app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
