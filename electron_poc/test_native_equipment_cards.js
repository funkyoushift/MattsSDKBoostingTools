"use strict";
const assert=require("node:assert/strict"),path=require("node:path"),fs=require("node:fs");
const {app,BrowserWindow,protocol}=require("electron");
const packagedResources=process.env.MSBT_CARD_PACKAGE_ROOT && path.resolve(process.env.MSBT_CARD_PACKAGE_ROOT,"resources");
const runtimeRoot=packagedResources ? path.join(packagedResources,"app.asar") : __dirname;
const nativeProtocol=require(path.join(runtimeRoot,"native_card_protocol"));
nativeProtocol.registerNativeCardSchemes(protocol);
app.whenReady().then(async()=>{
  nativeProtocol.installNativeCardProtocol(protocol);
  const resolver=require(path.join(runtimeRoot,"serial_card_resolve")).loadResolver({sourceRoot:packagedResources || path.resolve(__dirname,"..")});
  const fixtures=require("./fixtures/item_cards/equipped.json").slice(4);
  const win=new BrowserWindow({show:false,width:600,height:2200,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false,offscreen:true}});
  await win.loadFile(path.join(runtimeRoot,"renderer.html"),{query:{nosplash:"1"}});
  const output=path.resolve(__dirname,"../_tmp_native_card_preview");fs.mkdirSync(output,{recursive:true});
  for(const fixture of fixtures){
    const card=resolver.resolveFromHuman(fixture.human),equipment=card.native_equipment;
    assert.ok(equipment,card.item_type);
    assert.equal(card.stats_source,"offline_native_equipment");
    assert.ok(Number.isFinite(equipment.price));
    if(card.item_type==="Repkit")assert.equal(equipment.values.calc_ui_repair_kit_health_total,equipment.values.repair_kit_health_instant_value+equipment.values.repair_kit_health_over_time_value);
    if(card.item_type==="Enhancement")assert.ok(equipment.groups.secondary.some(row=>row.value.includes("+50%")),"enhancement must substitute the native percentage");
    if(card.item_type==="Ordnance"){
      const nuke=equipment.groups.secondary.find(row=>/nuke/.test(row.ident));
      assert.ok(nuke.value.includes("—"),"unverified modifier displays must not use final damage as a percentage");
      assert.ok(equipment.missing.includes("modifier_display:grenade_gadget_damage"));
    }
    if(card.item_type==="Classmod"){
      const primed=equipment.groups.primary.find(row=>row.name==="Primed and Ready");
      assert.equal(primed.points,5,"repeated passive tiers add to the same native node");
      assert.ok(primed.image.includes("ico_ui_art_passives"));
    }
    const result=await win.webContents.executeJavaScript(`(async()=>{
      const entry=applyOfflineCardToInventoryEntry({},${JSON.stringify(card)}),node=createBl4ItemCard(entry);
      node.style.cssText='position:absolute;left:10px;top:10px;width:546px;z-index:999999';
      document.querySelectorAll('dialog[open]').forEach(dialog=>dialog.close());document.body.replaceChildren(node);
      const frame=node.querySelector('iframe');frame.loading='eager';
      const deadline=Date.now()+15000;
      while(frame.dataset.rendered!=='true'&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,50));
      return {rendered:frame.dataset.rendered,errors:JSON.parse(frame.dataset.renderErrors||'[]'),height:frame.getBoundingClientRect().height};
    })()`);
    assert.equal(result.rendered,"true",card.item_type+JSON.stringify(result));assert.deepEqual(result.errors,[],card.item_type);
    const frame=win.webContents.mainFrame.frames.find(frame=>frame.url.startsWith("msbt-card:"));
    const details=await frame.executeJavaScript(`(()=>{const bounds=document.querySelector('.item_card').getBoundingClientRect();return {text:document.body.textContent,width:bounds.width,passives:document.querySelectorAll('.ic_class_mod_point_text').length,clipped:[...document.querySelectorAll('.item_card_class_mod_wrapper')].some(node=>{const box=node.getBoundingClientRect();return box.left<bounds.left-1 || box.right>bounds.right+1;})};})()`);
    assert.ok(details.text.includes(card.display_name));
    assert.ok(!details.text.includes("{mod"),"all dynamic description placeholders must be resolved or marked missing");
    if(card.item_type==="Classmod"){
      assert.equal(details.passives,equipment.groups.primary.length);
      assert.equal(details.clipped,false,"modded passive ranks must stay inside the card");
    }
    win.webContents.invalidate();await new Promise(resolve=>setTimeout(resolve,300));
    const capture=await win.webContents.capturePage({x:10,y:10,width:546,height:Math.min(2100,Math.ceil(result.height))});
    const bitmap=capture.toBitmap();let bright=0;for(let i=0;i<bitmap.length;i+=4)if(bitmap[i]>100||bitmap[i+1]>100||bitmap[i+2]>100)bright++;
    assert.ok(bright>10000,card.item_type+" must paint native artwork and text");
    fs.writeFileSync(path.join(output,"equipment-"+card.item_type.toLowerCase()+".png"),capture.toPNG());
    console.log("PASS",card.item_type,JSON.stringify({height:result.height,unresolved:equipment.missing}));
  }
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
