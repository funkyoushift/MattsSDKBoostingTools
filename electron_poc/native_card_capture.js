"use strict";

// Capture the whole extracted card at a fixed readable width, independent of
// the submit dialog's scroll position or the user's window size.
async function captureNativeCard(BrowserWindow, card) {
  if(card?.native_widget)return captureNativeWidget(BrowserWindow,card.native_widget);
  const {toNativeCardModel} = require("./native_card_model");
  const model = toNativeCardModel(card);
  return captureModel(BrowserWindow,model);
}

async function captureNativeWidget(BrowserWindow, widget) {
  return captureModel(BrowserWindow,require('./native_widget_card_model').fromNativeWidget(widget,{allowMissingArtwork:true}));
}

function makeCaptureWindow(BrowserWindow) {
  return new BrowserWindow({show:false, width:546, height:1200, useContentSize:true, frame:false,
    webPreferences:{sandbox:true, contextIsolation:true, nodeIntegration:false,
      offscreen:true, backgroundThrottling:false}});
}

function createNativeWidgetCapture(BrowserWindow) {
  let win=null,tail=Promise.resolve(),closed=false;
  return {
    capture(widget) {
      const model=require('./native_widget_card_model').fromNativeWidget(widget,{allowMissingArtwork:true});
      const job=tail.then(async()=>{
        if(closed)throw new Error('Native capture session is closed');
        if(!win||win.isDestroyed())win=makeCaptureWindow(BrowserWindow);
        try {return await captureModel(BrowserWindow,model,win);}
        catch(error) {
          // Chromium may lose the offscreen surface after many size changes.
          // Retry that capture once in a fresh window, with the same game data.
          if(!/UnknownVizError/.test(String(error?.message || error)))throw error;
          if(!win.isDestroyed())win.destroy();
          win=makeCaptureWindow(BrowserWindow);
          return captureModel(BrowserWindow,model,win);
        }
      });
      tail=job.catch(()=>{});return job;
    },
    async close(){closed=true;await tail;if(win&&!win.isDestroyed())win.destroy();win=null;}
  };
}

async function captureModel(BrowserWindow, model, existingWindow=null) {
  const win = existingWindow || makeCaptureWindow(BrowserWindow);
  try {
    await win.loadURL("msbt-card://inventory/card.html");
    const render = () => win.webContents.executeJavaScript(
      `renderNativeCard(${JSON.stringify(model)}, templates)`);
    let result = await render();
    if (result.errors?.length) throw new Error(result.errors.join("; "));
    const height = Math.ceil(result.height);
    if (!Number.isFinite(height) || height < 8 || height > 12000)
      throw new Error("Item card is too tall to capture safely.");
    // Keep the compositor surface below GPU dimension limits, including HiDPI.
    // Long native names can produce >16k physical pixels despite <12k CSS px.
    const tileHeight=2048;
    win.setContentSize(546, Math.min(height,tileHeight));
    result = await render();
    if (result.errors?.length) throw new Error(result.errors.join("; "));
    const tiles=[];
    for(let top=0;top<height;top+=tileHeight){
      await win.webContents.executeJavaScript(`(async()=>{
        document.getElementById('card-host').style.transform='translateY(-${top}px)';
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
      })()`);
      win.webContents.invalidate();
      const image=await win.webContents.capturePage({x:0,y:0,width:546,height:Math.min(tileHeight,height-top)});
      if(image.isEmpty())throw new Error('Item card capture was empty.');
      tiles.push(image);
    }
    // PNG pixels follow the monitor's DPI; retain that resolution and report
    // actual pixel dimensions rather than incorrectly treating them as CSS px.
    let png;
    if(tiles.length===1)png=tiles[0].toPNG();
    else {
      const rows=tiles.map(image=>{
        const data=image.toPNG(),width=data.readUInt32BE(16),height=data.readUInt32BE(20);
        const bitmap=image.toBitmap();
        if(bitmap.length!==width*height*4)throw new Error('Unexpected capture pixel scale');
        return {width,height,bitmap};
      });
      if(rows.some(row=>row.width!==rows[0].width))throw new Error('Capture scale changed between tiles');
      const {nativeImage}=require('electron');
      png=nativeImage.createFromBitmap(Buffer.concat(rows.map(row=>row.bitmap)),{
        width:rows[0].width,height:rows.reduce((sum,row)=>sum+row.height,0)}).toPNG();
    }
    return {ok:true, warnings:result.warnings || [], base64:png.toString("base64"), width:png.readUInt32BE(16),
      height:png.readUInt32BE(20), cssWidth:546, cssHeight:height};
  } finally {
    if (!existingWindow && !win.isDestroyed()) win.destroy();
  }
}

module.exports = {captureNativeCard,captureNativeWidget,createNativeWidgetCapture};
