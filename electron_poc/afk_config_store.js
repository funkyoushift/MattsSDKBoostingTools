/* IndexedDB keeps large loot lists outside localStorage's small string quota. */
(() => {
  const opened = new Promise((resolve, reject) => {
    const request = indexedDB.open('msbt-afk-settings', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('settings');
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  // Read failure is handled by the caller; do not emit an unhandled rejection.
  opened.catch(() => {});
  const access = async (mode, value) => {
    const db = await opened;
    return new Promise((resolve, reject) => {
      const tx = db.transaction('settings', mode);
      const store = tx.objectStore('settings');
      const request = mode === 'readonly' ? store.get('selection') : store.put(value, 'selection');
      tx.oncomplete = () => resolve(request.result);
      tx.onabort = () => reject(tx.error || Error('Settings could not be saved'));
      tx.onerror = () => reject(tx.error || request.error);
    });
  };
  window.msbtAfkConfigStore = { load: () => access('readonly'), save: value => access('readwrite', value) };
})();
