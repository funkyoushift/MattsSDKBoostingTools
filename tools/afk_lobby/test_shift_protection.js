'use strict';
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
const begin=source.indexOf('    function protectionSignature(names)');
const end=source.indexOf('    function handleSDKSaved()',begin);
assert(begin>=0 && end>begin);
const names=['local'];
const a={getProtectedNames:()=>names.slice(), setProtectedNames:v=>{names.splice(0,names.length,...new Set(v));},setSettings:()=>{}};
const c={window:{ShiftFriendAutomation:a},sdkDetected:false,sdkLastSeen:0,applyingSDK:false,sdkSettingsApplied:false, sdkRemoteReviewed:false, pendingProtection:null, saveAckReceived:false, sdkStorageState:"unavailable",sdkStateSeen:0,
 renderProtectedNames:()=>{},loadSettingsIntoControls:()=>{},updateStorageStatus:()=>{},Date};
vm.createContext(c);vm.runInContext(source.slice(begin,end),c);
c.handleSDKSettings({storageValid:false,protectedPlayers:['unsafe']});
assert.deepEqual(names,['local']);assert.equal(c.sdkDetected,false);
c.handleSDKSettings({storageValid:true,protectedPlayers:['remote'],settings:{}});
assert.deepEqual(names,['local','remote']);assert.equal(c.sdkDetected,true);
c.window.MsbtProtectionDirty=true; names.splice(names.indexOf('remote'),1);
c.handleSDKSettings({storageValid:true,protectedPlayers:['remote'],settings:{}});
assert.deepEqual(names,['local']);
c.handleSDKSettings('{invalid'); assert.equal(c.sdkDetected,false);assert.deepEqual(names,['local']);
console.log('PASS invalid and reconnect settings preserve local protection');
const saveStart=source.indexOf('    function saveSettingsNow()');
const saveEnd=source.indexOf('    function setupSDKBridge()',saveStart);
let sent=[]; const checkbox={pressed:"false",getAttribute:()=>checkbox.pressed,setAttribute:(k,v)=>{checkbox.pressed=v;}};
const saveCtx={window:{ShiftFriendAutomation:{getProtectedNames:()=>[],persistNow:()=>{}},setTimeout:()=>{}},
 currentStorageMode:'sdk',sdkDetected:false,sdkStorageState:'missing',sdkStateSeen:Date.now(),
 sdkLastSeen:0,saveAckReceived:false,pendingProtection:null,saveAckTimer:undefined,
 protectionSignature:()=> '[]',sendSettingsToSDK:v=>{sent.push(v);return true;},
 byId:()=>null,ensureProtectionReview:()=>checkbox,updateStorageStatus:()=>{},Date};
vm.createContext(saveCtx);vm.runInContext(source.slice(saveStart,saveEnd),saveCtx);
saveCtx.saveSettingsNow();assert.deepEqual(sent,[]);
checkbox.pressed="true";saveCtx.saveSettingsNow();assert.deepEqual(sent,[true]);
saveCtx.sdkStorageState='invalid';saveCtx.saveSettingsNow();assert.deepEqual(sent,[true]);
console.log('PASS explicit first-run review, empty list, and invalid storage guard');
const beforeAck=['saved'];
names.splice(0,names.length,...beforeAck);
c.window.MsbtProtectionDirty=true;c.window.MsbtProtectionReviewed=false;
c.pendingProtection=JSON.stringify(['saved']);c.saveAckReceived=false;
c.handleSDKSettings({storageValid:true,reviewed:true,protectedPlayers:['saved'],settings:{}});
assert.equal(c.window.MsbtProtectionReviewed,false);
c.saveAckReceived=true;
c.handleSDKSettings({storageValid:true,reviewed:true,protectedPlayers:['saved'],settings:{}});
assert.equal(c.window.MsbtProtectionReviewed,true);assert.equal(c.window.MsbtProtectionDirty,false);
console.log('PASS edited list requires save acknowledgement and matching readback');
const sendStart=source.indexOf('    var sdkPort = null');
const sendEnd=source.indexOf('    function notifySettingsChanged()',sendStart);
const requestStart=source.indexOf('    function requestSDKSettings()',sendEnd);
const requestEnd=source.indexOf('    function protectionSignature(',requestStart);
let requests=[], settings=[], acknowledgements=0;
class XHR {
  constructor(){requests.push(this);this.headers={};}
  open(method,url){this.method=method;this.url=url;}
  setRequestHeader(k,v){this.headers[k]=v;}
  send(body){this.body=body;}
  respond(status,data){this.status=status;this.responseText=JSON.stringify(data);this.onload();}
  fail(){this.onerror();}
}
const transfer={window:{MsbtProtectionReviewed:false},sdkRemoteReviewed:false,XMLHttpRequest:XHR,currentStorageMode:'sdk',sdkSending:false,sdkDetected:false,sdkLastSeen:0,sdkStorageState:'unavailable',saveAckReceived:false,
 compactPayload:()=>({s:{},n:['keep']}),handleSDKSettings:data=>settings.push(data),handleSDKSaved:()=>{acknowledgements++;},updateStorageStatus:()=>{}};
vm.createContext(transfer);vm.runInContext(source.slice(sendStart,sendEnd)+source.slice(requestStart,requestEnd),transfer);
const id='a'.repeat(32), response={ok:true,service:'msbt-shift-storage',protocol:1,instance:id,storageValid:true,storageState:'valid',settings:{},protectedPlayers:['keep'],reviewed:true};
transfer.requestSDKSettings(); assert.equal(requests[0].method,'GET');
requests[0].fail(); assert.match(requests[1].url,/:47992\//); requests[1].respond(200,response);
assert.equal(settings.length,1); assert.equal(transfer.sendSettingsToSDK(true),true);
const post=requests[2]; assert.equal(post.method,'POST'); assert.equal(post.headers['X-MSBT-Shift-Instance'],id);
assert.equal(JSON.parse(post.body).initialize,true); assert.equal(JSON.parse(post.body).reviewed,true);
transfer.requestSDKSettings(); assert.equal(requests.length,3);
post.respond(200,{...response,saved:true}); assert.equal(acknowledgements,1); assert.equal(settings.length,2);
assert.equal(transfer.sendSettingsToSDK(false),true); requests[3].respond(200,{...response,instance:'b'.repeat(32),saved:true});
assert.equal(acknowledgements,1); assert.equal(transfer.sdkDetected,false); assert.equal(transfer.sendSettingsToSDK(false),false);
transfer.requestSDKSettings(); requests[4].fail(); requests[5].fail(); requests[6].fail();
assert.equal(transfer.sdkDetected,false); assert.equal(requests.length,7);
console.log('PASS verified GET, bounded rotation, single POST and failed-save protection');

// Reopening starts with no in-memory review flag; only an explicit persisted marker
// and an identical local and SDK list restore readiness.
c.pendingProtection=null;c.saveAckReceived=false;c.window.MsbtProtectionReviewed=false;
c.window.MsbtProtectionDirty=false;
c.handleSDKSettings({storageValid:true,reviewed:true,protectedPlayers:['saved'],settings:{}});
assert.equal(c.window.MsbtProtectionReviewed,true);
c.window.MsbtProtectionReviewed=true; c.sdkRemoteReviewed=true;
c.handleSDKSettings({storageValid:true,protectedPlayers:['saved'],settings:{}});
assert.equal(c.window.MsbtProtectionReviewed,false);assert.equal(c.sdkRemoteReviewed,false);
console.log('PASS reviewed file survives reopen; legacy unreviewed file requires review');
const ensureStart=source.indexOf('    function ensureProtectionReview()');
const ensureEnd=source.indexOf('    window.MsbtSetProtectionReview',ensureStart);
let inserted=null, reviewNode=null;
const statusNode={parentNode:{insertBefore:(row)=>{inserted=row;reviewNode={pressed:"false",getAttribute(){return this.pressed;},setAttribute(k,v){this.pressed=v;}};}}};
const dom={document:{createElement:()=>({})},byId:id=>id==='shift_settings_storage_status'?statusNode:id==='shift_protection_review'?reviewNode:null};
vm.createContext(dom);vm.runInContext(source.slice(ensureStart,ensureEnd),dom);
assert.equal(dom.ensureProtectionReview(),reviewNode);
assert.match(inserted.innerHTML,/class="shift-settings-footer-btn primary"/);
assert.match(inserted.innerHTML,/role="button"/);
assert.match(inserted.innerHTML,/aria-pressed="false"/);
assert.match(inserted.innerHTML,/empty, no friends are protected/);
console.log('PASS in-page review button renders empty-list meaning');
const toggleStart=source.indexOf('    window.MsbtSetProtectionReview');
const toggleEnd=source.indexOf('    function saveSettingsNow()',toggleStart);
const toggleContext={window:{},byId:()=>reviewNode};
vm.createContext(toggleContext);vm.runInContext(source.slice(toggleStart,toggleEnd),toggleContext);
toggleContext.window.MsbtToggleProtectionReview();assert.equal(reviewNode.pressed,'true');
assert.match(reviewNode.textContent,/Reviewed/);
toggleContext.window.MsbtResetProtectionReview();assert.equal(reviewNode.pressed,'false');
assert.match(reviewNode.textContent,/Not reviewed/);
console.log('PASS review button toggles accessible state and resets after edits');
const readinessMatch=source.match(/protectionReady: function \(\) \{[^}]+\}/);
assert.ok(readinessMatch);
vm.runInContext('function protectionReady() {' + readinessMatch[0].split('{')[1],c);
c.currentStorageMode='sdk'; c.window.MsbtProtectionDirty=false;
c.handleSDKSettings({storageValid:true,reviewed:true,protectedPlayers:['saved'],settings:{}});
assert.equal(c.protectionReady(),true);
const failureStart=source.indexOf('    function bridgeFailed()');
const failureEnd=source.indexOf('    function sendSettingsToSDK(',failureStart);
c.sdkPort=47991;c.sdkInstance='a'.repeat(32);
vm.runInContext(source.slice(failureStart,failureEnd),c);
c.bridgeFailed();assert.equal(c.protectionReady(),false);
c.handleSDKSettings({storageValid:true,reviewed:false,protectedPlayers:['saved'],settings:{}});
assert.equal(c.sdkDetected,true);assert.equal(c.protectionReady(),false);
console.log('PASS reconnect to unreviewed settings cannot inherit prior review');

c.window.MsbtSetProtectionReview=toggleContext.window.MsbtSetProtectionReview;
c.window.MsbtResetProtectionReview=toggleContext.window.MsbtResetProtectionReview;
names.splice(0,names.length,'saved'); c.window.MsbtProtectionDirty=false; c.window.MsbtProtectionReviewed=false;
c.handleSDKSettings({storageValid:true,reviewed:true,protectedPlayers:['saved'],settings:{}});
assert.equal(reviewNode.pressed,'true'); assert.match(reviewNode.textContent,/Reviewed/);
c.handleSDKSettings({storageValid:true,reviewed:false,protectedPlayers:['saved'],settings:{}});
assert.equal(reviewNode.pressed,'false'); assert.equal(c.window.MsbtProtectionReviewed,false);
toggleContext.window.MsbtToggleProtectionReview();
c.handleSDKSettings({storageValid:false,storageState:'missing'}); assert.equal(reviewNode.pressed,'true');
c.handleSDKSettings({storageValid:false,storageState:'invalid'}); assert.equal(reviewNode.pressed,'false');
console.log('PASS review display follows stored state and preserves first-run review');

// Undoing a verified review blocks readiness and cannot be silently restored by a poll.
reviewNode.pressed='true'; toggleContext.window.MsbtProtectionReviewed=true; toggleContext.window.MsbtProtectionDirty=false;
toggleContext.window.MsbtToggleProtectionReview();
assert.equal(toggleContext.window.MsbtProtectionReviewed,false); assert.equal(toggleContext.window.MsbtProtectionDirty,true);
assert.equal(reviewNode.pressed,'false');
c.window.MsbtProtectionReviewed=toggleContext.window.MsbtProtectionReviewed; c.window.MsbtProtectionDirty=toggleContext.window.MsbtProtectionDirty;
c.handleSDKSettings({storageValid:true,reviewed:true,protectedPlayers:['saved'],settings:{}});
assert.equal(c.window.MsbtProtectionReviewed,false); assert.equal(reviewNode.pressed,'false');
// A first-time unchecked toggle does not itself mark the list dirty.
toggleContext.window.MsbtProtectionReviewed=false; toggleContext.window.MsbtProtectionDirty=false; reviewNode.pressed='false';
toggleContext.window.MsbtToggleProtectionReview(); toggleContext.window.MsbtToggleProtectionReview();
assert.equal(toggleContext.window.MsbtProtectionDirty,false);
console.log('PASS undo revokes verified review until explicit save');

// A new user starts empty; existing browser-saved names remain untouched.
const defaultsStart=source.indexOf('    var PROTECTED_NAMES_STORAGE_KEY =');
const defaultsEnd=source.indexOf('    window.MsbtProtectionDirty = false;',defaultsStart);
assert(defaultsStart>=0 && defaultsEnd>defaultsStart);
function readInitial(value) {
  let stored=value; const ctx={window:{localStorage:{getItem:()=>stored,setItem:(k,v)=>{stored=v;}}}};
  vm.createContext(ctx); vm.runInContext(source.slice(defaultsStart,defaultsEnd),ctx);
  return {names:Array.from(ctx.readProtectedNames()),stored};
}
const newUser=readInitial(null); assert.deepEqual(newUser.names,[]); assert.equal(newUser.stored,'[]');
const existing=readInitial('["Existing User"]'); assert.deepEqual(existing.names,['Existing User']); assert.equal(existing.stored,'["Existing User"]');
console.log('PASS first-run list empty; previously saved names retained');
