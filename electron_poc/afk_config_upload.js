/* Transfer large settings without changing serials, order, or duplicate entries. */
(function (root) {
  async function send(action, payload, request, supported) {
    const bytes = new TextEncoder().encode(JSON.stringify(payload));
    if (action !== 'afk_lobby_start' || bytes.length < 512 * 1024) return request(action, payload);
    if (!supported) throw Error('Update the SDK mod and restart Borderlands to use large AFK loot lists. Your saved lists have been kept.');
    const checked = async (name, data) => {
      const response = await request(name, data);
      const result = response?.data ?? response;
      if (!result || result.ok !== true || result.queued) throw Error(result?.message || 'AFK list transfer was not confirmed. Start again.');
      return result;
    };
    const { token } = await checked('afk_config_upload', { mode: 'begin' });
    let committing = false;
    try {
      let count = 0;
      for (let offset = 0; offset < bytes.length; offset += 192 * 1024) {
        const chunk = bytes.subarray(offset, offset + 192 * 1024);
        let binary = '';
        for (let i = 0; i < chunk.length; i += 8192) binary += String.fromCharCode(...chunk.subarray(i, i + 8192));
        const result = await checked('afk_config_upload', { mode: 'append', token, index: count, data: btoa(binary) });
        count++;
        if (result.count !== count) throw Error('AFK list transfer acknowledgement did not match. Start again.');
      }
      const hash = await crypto.subtle.digest('SHA-256', bytes);
      const sha256 = Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, '0')).join('');
      committing = true;
      return await request('afk_lobby_start_uploaded', { token, count, size: bytes.length, sha256 });
    } finally {
      // Commit consumes the file; cancellation also cleans up interrupted transfers.
      if (!committing) {
        try { await request('afk_config_upload', { mode: 'cancel', token }); } catch (_) {}
      }
    }
  }
  root.msbtAfkConfigSend = send;
  if (typeof module !== 'undefined') module.exports = send;
})(typeof window !== 'undefined' ? window : globalThis);
