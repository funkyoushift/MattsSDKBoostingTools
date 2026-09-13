// Diagnostic Chromium host for extracted Cohtml templates. No game or IPC API.
// This adapts bindings; it does NOT recreate native naming/stat calculations.
class GbxCustomElement extends HTMLElement { Init() {} connectedCallback() {} }
class Widget_OakHUDWidgetBase extends GbxCustomElement {}
const TooltipMgr = {};
// English defaults from the extracted gbxmain.js. No engine event bus offline.
const LanguageSettings = {CurrentLangCode: "en", DisableNBSPMarkup: false};
const errors = [];
function safeMarkup(value) {
  // Item strings are data. Escape HTML before expanding the game's bracket
  // markup so imported serial metadata cannot create executable DOM elements.
  return String(value ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
function valueOf(expression, scope) {
  const values = [];
  const code = expression.replace(/\{\{([^}]+)\}\}/g, (_, key) => {
    let value = scope;
    for (const part of key.trim().split(".")) value = value?.[part];
    values.push(value);
    return `v[${values.length - 1}]`;
  });
  // Expressions are read only from original extracted game templates, never
  // constructed from an item name or another data-model string.
  try { return Function("v", `"use strict"; return (${code});`)(values); }
  catch (error) { errors.push(`${expression}: ${error.message}`); return undefined; }
}
function bindNode(node, scope) {
  if (node.nodeType !== 1) return;
  const loop = node.getAttribute("data-bind-for");
  if (loop) {
    const colon = loop.indexOf(":"), names = loop.slice(0, colon).split(",").map(s => s.trim());
    const rows = valueOf(loop.slice(colon + 1), scope) || [];
    rows.forEach((entry, index) => {
      const copy = node.cloneNode(true); copy.removeAttribute("data-bind-for");
      const childScope = {...scope, [names.at(-1)]:entry};
      if (names.length > 1) childScope[names[0]] = index;
      node.before(copy); bindNode(copy, childScope);
    });
    node.remove(); return;
  }
  const condition = node.getAttribute("data-bind-if");
  if (condition && !valueOf(condition, scope)) { node.remove(); return; }
  for (const attr of [...node.attributes]) {
    const expression = attr.value;
    if (attr.name === "data-bind-value") node.textContent = valueOf(expression, scope) ?? "";
    else if (attr.name === "data-bind-markup") node.innerHTML = MarkupMgr.ResolveMarkupText(safeMarkup(valueOf(expression, scope)));
    else if (attr.name === "data-bind-class") {
      const classes = String(valueOf(expression, scope) || "").split(/\s+/).filter(Boolean);
      node.classList.add(...classes);
    } else if (attr.name === "data-bind-class-toggle") {
      for (const toggle of expression.split(";")) {
        const colon = toggle.indexOf(":");
        node.classList.toggle(toggle.slice(0, colon), Boolean(valueOf(toggle.slice(colon+1), scope)));
      }
    } else if (attr.name === "data-bind-style-background-image-url") {
      const url = valueOf(expression, scope);
      if (typeof url === "string" && /^(coui|common):\/\/uiresources\//i.test(url)) node.style.backgroundImage = `url(${JSON.stringify(url)})`;
      if(scope.entry?.name)node.title=scope.entry.name;
    } else if (attr.name === "data-bind-oak-rarity") node.setAttribute("oak-rarity", valueOf(expression, scope) || "");
  }
  for (const child of [...node.children]) bindNode(child, scope);
}
async function renderNativeCard(model, templates) {
  errors.length = 0;
  const host = document.getElementById("card-host");
  const original = new DOMParser().parseFromString(templates.item_card, "text/html");
  original.querySelectorAll("script,link").forEach(n => n.remove());
  host.replaceChildren(...original.body.children);
  bindNode(host, {$data:model});
  // Modded class mods can exceed the game's normal three skill rows. Keep
  // every extracted rank visible within the card instead of clipping sideways.
  host.classList.toggle("extended-passives",!!model.extendedpassives);
  for (const component of host.querySelectorAll("gbx-component")) {
    const key = component.getAttribute("gbx-component-id");
    if (!templates[key]) { errors.push(`Unsupported visible component: ${key}`); continue; }
    const doc = new DOMParser().parseFromString(templates[key], "text/html");
    doc.querySelectorAll("script,link").forEach(n => n.remove());
    component.replaceChildren(...doc.body.children);
  }
  for (const node of host.querySelectorAll("rarity-pips,elemental-damagetype")) node.Init();
  const card = host.querySelector("widget-item-card");
  card.Init(); card.DataModel = model; card.UpdateDamageType();
  await document.fonts.ready;
  // CSS backgrounds and border artwork are asynchronous too. Wait for every
  // computed resource before capture instead of accepting an incomplete frame.
  const imageUrls = new Set();
  for (const node of host.querySelectorAll("*")) {
    const style = getComputedStyle(node);
    for (const css of [style.backgroundImage, style.borderImageSource])
      for (const match of css.matchAll(/url\(["']?([^"')]+)["']?\)/g)) imageUrls.add(match[1]);
  }
  await Promise.all([...imageUrls].map(url => new Promise(resolve => {
    const image = new Image(); image.onload = resolve;
    image.onerror = () => {errors.push(`Image failed: ${url}`); resolve();};
    image.src = url;
  })));
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  return {errors, name:host.querySelector('.item_card_name')?.textContent || model.name,
    width:host.querySelector('.item_card').getBoundingClientRect().width,
    height:host.querySelector('.item_card').getBoundingClientRect().height};
}
