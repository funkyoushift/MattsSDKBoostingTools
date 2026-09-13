"use strict";
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const schemes = ["coui","common","msbt-card"];
function registerNativeCardSchemes(protocol) {
  protocol.registerSchemesAsPrivileged(schemes.map(scheme => ({scheme,privileges:{standard:true,secure:true,supportFetchAPI:true}})));
}
function createNativeCardDocument(root = path.join(__dirname,"native_card_ui")) {
  const read = file => fs.readFileSync(path.join(root,file),"utf8");
  const templates = Object.fromEntries(["item_card","rarity_pips","element_damage_type"].map(name => [name,
    read(name === "item_card" ? `uiresources/${name}/${name}.html` : `uiresources/components/${name}/${name}.html`)]));
  const filters = new Map();
  const css = content => content.replace(/coh-color-matrix\(([^)]+)\)/g,(_,values) => {
    const id = "matrix"+crypto.createHash("sha256").update(values).digest("hex").slice(0,12);
    filters.set(id,values.replace(/,/g," ")); return `url(#${id})`;
  }).replace(/(?<!-)\btext-stroke(?=-|:)/g,"-webkit-text-stroke").replace(/@media \(language: None\)/g,"@media all");
  const styles = ["_shared/css/gbx.css","_shared/css/oakgame.css","_shared/css/oak_icons.css","_shared/css/oak_markup.css","_shared/css/oak_tooltip.css","_shared/css/color_tint_filters.css","item_card/css/item_card.css","components/rarity_pips/css/rarity_pips.css","components/element_damage_type/css/element_damage_type.css"].map(file => css(read("uiresources/"+file))).join("\n")
    + css(read("DLC/Common/uiresources/dlc_rarity_pips/css/dlc_rarity_pips.css"));
  const scripts = ["_shared/js/markup_manager.js","components/rarity_pips/js/rarity_pips.js","components/element_damage_type/js/element_damage_type.js","item_card/js/item_card.js"].map(file => read("uiresources/"+file));
  const script = content => `<script>${content.replace(/<\/script/gi,"<\\/script")}</script>`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>${styles}</style>
<style>${fs.readFileSync(path.join(__dirname,"native_card_compat.css"),"utf8")}
html{font-size:10px;height:100vh}body{background:transparent;overflow:hidden;height:100vh}#card-host{position:relative;margin:0}widget-item-card{position:relative;display:block}widget-item-card>br{display:none}.tooltip_container{opacity:1!important;visibility:visible!important;transform:none!important}svg#filters{position:absolute;width:0;height:0}
</style></head><body><svg id="filters"><defs>${[...filters].map(([id,v])=>`<filter id="${id}" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="${v}"/></filter>`).join("")}</defs></svg><div id="card-host"></div>
${script(fs.readFileSync(path.join(__dirname,"native_card_adapter.js"),"utf8"))}${scripts.map(script).join("")}
${script(`const MarkupMgr=new MarkupManager();const templates=${JSON.stringify(templates)};
let pending=null,running=false;
function fit(){document.documentElement.style.fontSize=(innerWidth/54.6)+'px';const card=document.querySelector('.item_card');if(card)parent.postMessage({type:'msbt-card-size',height:Math.ceil(card.getBoundingClientRect().bottom)},'*');}
addEventListener('resize',fit);
addEventListener('message',async event=>{if(event.source!==parent||event.data?.type!=='msbt-card-model')return;pending=event.data.model;if(running)return;running=true;try{while(pending){const model=pending;pending=null;fit();const result=await renderNativeCard(model,templates);fit();parent.postMessage({type:'msbt-card-rendered',...result},'*');}}catch(error){parent.postMessage({type:'msbt-card-error',message:error.message},'*');}finally{running=false;}});
parent.postMessage({type:'msbt-card-ready'},'*');`)}
</body></html>`;
}
function installNativeCardProtocol(protocol, root = path.join(__dirname,"native_card_ui")) {
  let document;
  protocol.handle("msbt-card", request => {
    const url = new URL(request.url);
    if (url.hostname !== "inventory" || url.pathname !== "/card.html") return new Response("Missing",{status:404});
    document ||= createNativeCardDocument(root);
    return new Response(document,{headers:{"Content-Type":"text/html; charset=utf-8"}});
  });
  for (const scheme of ["coui","common"]) protocol.handle(scheme, request => {
    const url = new URL(request.url);
    if (url.hostname !== "uiresources") return new Response("Missing",{status:404});
    const file = path.resolve(root,scheme === "common" ? "DLC/Common" : "",url.hostname+decodeURIComponent(url.pathname));
    if (!file.toLowerCase().startsWith((path.resolve(root)+path.sep).toLowerCase()) || !fs.existsSync(file) || !fs.statSync(file).isFile())
      return new Response("Missing",{status:404});
    const mime = {".png":"image/png",".ttf":"font/ttf",".svg":"image/svg+xml",".css":"text/css"}[path.extname(file).toLowerCase()];
    if (!mime) return new Response("Unsupported resource",{status:403});
    return new Response(fs.readFileSync(file),{headers:{"Content-Type":mime,"Access-Control-Allow-Origin":"*"}});
  });
}
module.exports = {registerNativeCardSchemes,installNativeCardProtocol,createNativeCardDocument};
