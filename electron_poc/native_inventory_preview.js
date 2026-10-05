"use strict";
(function(root) {
  // Bound IPC demand, not inventory size. The main process serializes native
  // work and keeps its own queue guard for unrelated callers.
  async function enrich(entries, preview, onProgress = () => {}) {
    const result = entries.slice(), requests = new Map();
    let next = 0, completed = 0;
    async function worker() {
      while (next < entries.length) {
        const index = next++, entry = entries[index];
        if (entry?.serial) {
          try {
            if (!requests.has(entry.serial)) requests.set(entry.serial,
              Promise.resolve().then(() => preview(entry.serial, false)));
            const reply = await requests.get(entry.serial);
            if (!reply?.ok || !reply.widget) throw new Error(reply?.message || 'Game card unavailable');
            const widget = reply.widget;
            result[index] = {...entry, display_name:widget.Name, item_type:widget.WhiteHeader,
              rarity:widget.RarityLoc, manufacturer:widget.ManufacturerName,
              native_widget:widget, native_level_text:widget.Level,
              meta_source:'native_game', name_status:'complete'};
            delete result[index].native_preview_error;
          } catch (error) {
            result[index] = {...entry, display_name:'Card unavailable',
              native_widget:null, native_preview_error:error.message, name_status:'unverified'};
          }
        }
        onProgress(++completed, entries.length);
      }
    }
    await Promise.all(Array.from({length:Math.min(8, entries.length)}, worker));
    return result;
  }
  if (typeof module === 'object' && module.exports) module.exports = {enrich};
  else root.MSBTNativeInventoryPreview = {enrich};
})(typeof window === 'object' ? window : globalThis);
