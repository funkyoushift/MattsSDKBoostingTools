'use strict';
// An inventory record need not carry catalog metadata. Match the full, case-sensitive
// serial before considering an external renderer; never match by item name.
function gzoImageIndex(rows) {
  const index = new Map();
  for (const row of rows || []) {
    const serial = row.serial || row.base85;
    try {
      const url = new URL(row.image_url || row.image);
      if (typeof serial !== 'string' || url.protocol !== 'https:' ||
          url.hostname !== 'save-editor.be' || !url.pathname.startsWith('/GZO/')) continue;
      index.set(serial, {state:'ready', source:'gzo', image:url.href, itemCard:{name:row.name || ''}});
    } catch { /* No usable catalog image. */ }
  }
  return index;
}
function resolveImageRequests(serials, images, cache, operation, priority, identities=new Map(), equivalentImages=new Map(), representatives=new Map()) {
  return serials.map(serial => {
    const key=identities.get(serial);
    const image=images.get(serial)||(key&&equivalentImages.get(key));
    if(image)return {serial,...image,match:images.has(serial)?'exact':'equivalent'};
    const representative=(key&&representatives.get(key))||serial;
    if(key&&operation==='demand'&&!representatives.has(key))representatives.set(key,serial);
    return {serial,...(operation==='demand'?cache.demand(representative,priority):cache.lookup(representative))};
  });
}
module.exports = {gzoImageIndex, resolveImageRequests};
