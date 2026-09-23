"use strict";

// Capture the whole extracted card at a fixed readable width, independent of
// the submit dialog's scroll position or the user's window size.
async function captureNativeCard(BrowserWindow, card) {
  const {toNativeCardModel} = require("./native_card_model");
  const model = toNativeCardModel(card);
  const win = new BrowserWindow({show:false, width:546, height:1200,
    webPreferences:{sandbox:true, contextIsolation:true, nodeIntegration:false,
      offscreen:true, backgroundThrottling:false}});
  try {
    await win.loadURL("msbt-card://inventory/card.html");
    const render = () => win.webContents.executeJavaScript(
      `renderNativeCard(${JSON.stringify(model)}, templates)`);
    let result = await render();
    if (result.errors?.length) throw new Error(result.errors.join("; "));
    const height = Math.ceil(result.height);
    if (!Number.isFinite(height) || height < 8 || height > 12000)
      throw new Error("Item card is too tall to capture safely.");
    win.setContentSize(546, height);
    result = await render();
    if (result.errors?.length) throw new Error(result.errors.join("; "));
    win.webContents.invalidate();
    const image = await win.webContents.capturePage({x:0,y:0,width:546,height});
    if (image.isEmpty()) throw new Error("Item card capture was empty.");
    // PNG pixels follow the monitor's DPI; retain that resolution and report
    // actual pixel dimensions rather than incorrectly treating them as CSS px.
    const png = image.toPNG();
    return {ok:true, base64:png.toString("base64"), width:png.readUInt32BE(16),
      height:png.readUInt32BE(20), cssWidth:546, cssHeight:height};
  } finally {
    if (!win.isDestroyed()) win.destroy();
  }
}

module.exports = {captureNativeCard};
