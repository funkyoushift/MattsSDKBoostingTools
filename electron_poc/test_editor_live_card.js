'use strict';
const {app,BrowserWindow}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const win=new BrowserWindow({show:false,width:1500,height:1000,webPreferences:{partition:'editor-cards-'+process.pid}});
 const adapter=fs.readFileSync(path.join(__dirname,'../external_app/v22_parts_codes_fixed/matt_editor_adapter.js'),'utf8');
 const fixture='<script>window.addEventListener("message",e=>{if(e.source===parent&&e.data.testEditorCodes)document.getElementById("serializedOutput").value=e.data.testEditorCodes.join("\\n");});</script><div class="tab-content active" id="edit"><textarea id="serializedOutput"></textarea></div><div class="tab-content" id="other"><textarea id="finalOutputBase85">@UHidden0000000000000000</textarea></div>';
 await win.webContents.session.protocol.handle('https',request=>new Response(request.url.endsWith('/adapter.js')?adapter:fixture+'<script src="/adapter.js"></script>',{headers:{'Content-Type':request.url.endsWith('.js')?'application/javascript':'text/html'}}));
 await win.loadURL('data:text/html,'+encodeURIComponent('<section id="tab-matt-editor" class="active"><iframe id="editorFrame"></iframe><input type="checkbox" checked id="editorCardAuto"><select id="editorCardChoice"></select><button id="editorCardRefresh">Refresh</button><div id="editorLiveCardStatus"></div><div id="editorLiveCard"></div></section>'));
 await win.webContents.executeJavaScript(fs.readFileSync(path.join(__dirname,'editor_live_card.js'),'utf8'));
 const result=await win.webContents.executeJavaScript(`(async()=>{
  const sleep=ms=>new Promise(r=>setTimeout(r,ms)),check=(v,m)=>{if(!v)throw Error(m);};
  const frame=document.getElementById('editorFrame'),page=document.getElementById('tab-matt-editor');
  const host=document.getElementById('editorLiveCard'),auto=document.getElementById('editorCardAuto');
  let requests=[],release,active=0,maxActive=0;
  window.MSBTItemCards={};window.MSBTItemCards.show=(node,item)=>{
    requests.push(item.serial);active++;maxActive=Math.max(maxActive,active);
    const marker=document.createElement('div');node.replaceChildren(marker);
    node.cardRequest=new Promise(r=>{release=()=>{if(node.contains(marker))marker.textContent=item.serial;active--;r();};});return node;
  };
  page.classList.add('active');
  await new Promise(r=>{frame.addEventListener('load',r,{once:true});frame.src='https://editor.test/?msbtShell=1';});
  // Drive the real adapter in a cross-origin iframe through a test-only command.
  const serials=['@UFirst000000000000000000','@USecond00000000000000000','@UThird000000000000000000'];
  window.dispatchEvent(new MessageEvent('message',{source:frame.contentWindow,origin:'https://evil.test',data:{msbtEditorCard:{serials:[serials[0]]}}}));
  await sleep(1100);check(!requests.length,'wrong origin accepted');
  const send=values=>frame.contentWindow.postMessage({testEditorCodes:values},'https://editor.test');
  send([serials[0]]);await sleep(100);send([serials[1]]);await sleep(1100);
  check(requests.length===1&&requests[0]===serials[1],'rapid edits must coalesce');
  send([serials[2]]);await sleep(1100);check(requests.length===1,'queued parallel native work');
  release();await sleep(1100);check(requests[1]===serials[2]&&!host.textContent.includes(serials[1]),'stale card or latest edit lost');release();await sleep(20);
  send([serials[2]]);await sleep(1100);check(requests.length===2,'unchanged serial rerendered');
  send([]);await sleep(300);check(!host.textContent,'invalid output left old card visible');
  send([serials[0],serials[1]]);await sleep(1100);check(requests.length===2,'bulk output rendered automatically');
  const choice=document.getElementById('editorCardChoice');choice.value=serials[0];choice.dispatchEvent(new Event('change'));await sleep(1100);check(requests.at(-1)===serials[0],'bulk choice ignored');release();await sleep(10);
  auto.checked=false;auto.dispatchEvent(new Event('change'));send([serials[2]]);await sleep(1100);check(requests.length===3,'pause ignored');
  document.getElementById('editorCardRefresh').click();await sleep(1100);check(requests.length===4,'manual refresh ignored');release();await sleep(10);
  page.classList.remove('active');auto.checked=true;auto.dispatchEvent(new Event('change'));send([serials[0]]);await sleep(1100);check(requests.length===4,'hidden editor rendered');
  page.classList.add('active');await sleep(1100);check(requests.length===5,'editor resume did not render');release();
  return {coalesced:true,staleDiscarded:true,oneAtATime:maxActive===1,bulkSelection:true,paused:true,hidden:true,originChecked:true};
 })()`);
 assert(result.oneAtATime);console.log(JSON.stringify(result));win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});

