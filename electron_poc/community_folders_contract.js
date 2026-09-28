/* Data-only community folders. Shared by the desktop and service validator. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.communityFolderContract = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  const MAX_BYTES = 16 * 1024 * 1024;
  const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  function text(value, label, max, required = false) {
    if (typeof value !== 'string') throw Error(`${label} must be text.`);
    value = value.trim();
    if ((required && !value) || value.length > max || /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(value)) throw Error(`${label} is empty, too long, or contains control characters.`);
    return value;
  }
  function folderPath(value) {
    value = text(value, 'Subfolder', 160);
    if (!value) return '';
    const parts = value.split('/').map(s => s.trim());
    if (parts.some(s => !s || s === '.' || s === '..' || /[\\]/.test(s))) throw Error('Invalid subfolder path.');
    return parts.join(' / ');
  }
  function normalize(input) {
    if (!input || input.version !== 1 || !Array.isArray(input.items) || !input.items.length) throw Error('Choose a folder containing items.');
    const out = {version:1, title:text(input.title,'Folder title',80,true), creator:text(input.creator,'Display name',80,true), description:text(input.description || '','Description',2000), folders:[], items:[]};
    out.folders = [...new Set((input.folders || []).map(folderPath))];
    out.items = input.items.map((item, index) => {
      if (!item || typeof item.serial !== 'string' || !/^@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{/}~]+$/.test(item.serial)) throw Error(`Item ${index + 1} is not one encoded @U code.`);
      return {name:text(item.name || `Saved item ${index + 1}`,'Item name',180,true), folder:folderPath(item.folder || ''), serial:item.serial};
    });
    if (new TextEncoder().encode(JSON.stringify(out)).length > MAX_BYTES) throw Error('This folder exceeds the 16 MB sharing size. Split it into smaller folders; nothing was uploaded.');
    return out;
  }
  function exportFolder(bookmarks, folders, selected, details) {
    if (!selected) throw Error('Choose a bookmark folder to submit.');
    const canonical = name => String(name).split('/').map(s=>s.trim()).join(' / ');
    selected = canonical(selected);
    bookmarks = bookmarks.map(row=>({...row,group:canonical(row.group || 'Default')}));
    folders = folders.map(canonical);
    const within = name => name === selected || name.startsWith(selected + ' / ');
    const relative = name => name === selected ? '' : name.slice(selected.length + 3);
    return normalize({version:1,...details, folders:folders.filter(within).map(relative),items:bookmarks.filter(row => within(row.group || 'Default')).map(row => ({name:row.name,serial:row.serial,folder:relative(row.group || 'Default')}))});
  }
  function importFolder(data, existing, idFactory, requestedName) {
    const folder = normalize(data);
    const names = new Set([...(existing.folders || []),...existing.bookmarks.map(row=>row.group || 'Default')]);
    const base = text(requestedName || folder.title,'Destination folder',80,true).replace(/[\\/]/g,'-');
    let destination=base, n=2;
    while ([...names].some(name=>name===destination || name.startsWith(destination+' / '))) destination=`${base} (${n++})`;
    const path = relative => {
      const result = relative ? destination + ' / ' + relative : destination;
      if(result.length>180) throw Error('A subfolder path is too long to import. Choose a shorter destination name.');
      return result;
    };
    const now=new Date().toISOString();
    const rows=folder.items.map(item=>({id:idFactory(),name:item.name,serial:item.serial,group:path(item.folder),created_at:now,updated_at:now,source:'Community folder'}));
    return {destination,version:1,bookmarks:[...existing.bookmarks,...rows],folders:[...new Set([...names,destination,...folder.folders.map(path),...rows.map(row=>row.group)])]};
  }
  return {MAX_BYTES,ID,normalize,exportFolder,importFolder};
});
