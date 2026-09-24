"use strict";

// Preserve request order and prevent concurrent saves sharing a .tmp file.
const pending = new Map();
function queueSettingsWrite(filePath, write) {
  const previous = pending.get(filePath) || Promise.resolve();
  const next = previous.catch(() => {}).then(write);
  pending.set(filePath, next);
  const cleanup = () => {
    if (pending.get(filePath) === next) pending.delete(filePath);
  };
  next.then(cleanup, cleanup);
  return next;
}
module.exports = { queueSettingsWrite };
