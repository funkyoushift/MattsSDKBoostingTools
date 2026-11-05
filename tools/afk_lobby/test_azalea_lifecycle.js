// Runs extracted PAK code with a clock and native calls simulated; no SHiFT traffic.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const text = fs.readFileSync(process.argv[2], 'utf8');
const begin = text.indexOf('var ShiftFriendAutomation = (function ()');
const end = text.indexOf('window.ShiftFriendAutomation = ShiftFriendAutomation;', begin);
assert(begin > 0 && end > begin);
function setup(saved = {}) {
  let clock = 0, next = 0;
  const timers = new Map(), handlers = new Map(), calls = [], storage = new Map(Object.entries(saved));
  const timer = (fn, delay, repeat = false) => { const id = ++next; timers.set(id, {fn, at:clock+delay, delay, repeat}); return id; };
  const context = {
    window: {ShiftMiniPanel:{protectionReady:()=>true},localStorage:{getItem:k=>storage.has(k)?storage.get(k):null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
      setTimeout:(fn,d)=>timer(fn,d),clearTimeout:id=>timers.delete(id),
      setInterval:(fn,d)=>timer(fn,d,true),clearInterval:id=>timers.delete(id)},
    document:{getElementById:()=>null},
    friends_model:{receivedRequestsList:[],allInvites:[],friendsList:[]},
    friends_controller:{showSuccessMessage:()=>{},hideSuccessMessage:()=>{},showErrorMessage:()=>{},hideErrorMessage:()=>{}},
    engine:{on:(k,fn)=>handlers.set(k,fn),off:k=>handlers.delete(k),call:(...args)=>calls.push(args)}
  };
  for (const key of ['FRIENDS_LOAD_REQUEST_LIST_RESPONSE','FRIENDS_LOAD_REQUEST_LIST_CALL','FRIENDS_LOAD_FRIENDS_LIST_CALL',
    'FRIENDS_PLAYER_PROFILE_GAME_INVITE','PLAYER_PROFILE_MENU_ACCEPT_REQUEST','PLAYER_PROFILE_MENU_DECLINE_REQUEST',
    'FRIENDS_NOTIFICATION_DECLINE_GAME_INVITE','FRIENDS_NOTIFICATION_GAME_INVITE','PLAYER_PROFILE_MENU_REMOVE','FRIENDS_OFFLINE']) context[key]=key;
  vm.createContext(context); vm.runInContext(text.slice(begin,end),context);
  return {a:context.ShiftFriendAutomation, context, calls, storage,
    respond:rows=>handlers.get('FRIENDS_LOAD_REQUEST_LIST_RESPONSE')?.(rows),
    actions:()=>calls.filter(c=>!c[0].startsWith('FRIENDS_LOAD_')),
    advance(ms) { const until=clock+ms; for(let n=0;n<1000;n++) {
      const first=[...timers].filter(([,t])=>t.at<=until).sort((a,b)=>a[1].at-b[1].at)[0];
      if(!first) { clock=until; return; }
      const [id,t]=first; clock=t.at; if(t.repeat)t.at+=t.delay;else timers.delete(id);t.fn();
    } throw Error('unbounded timer loop'); }
  };
}
let failed=0, passed=0;
function test(name,fn) {try{fn();passed++;console.log('PASS '+name);}catch(e){failed++;console.error('FAIL '+name+': '+e.message);}}
const incoming=[{id:'a',sent:false},{id:'b',sent:false},{id:'outgoing',sent:true}];
test('Save preserves protected names across page reload',()=>{
  const s=setup();s.a.setProtectedNames(['Keep Me']);s.a.persistNow();
  assert.deepEqual(Array.from(setup(Object.fromEntries(s.storage)).a.getProtectedNames()),['Keep Me']);
});
test('empty authoritative response never replays cached requests',()=>{
  const s=setup();s.context.friends_model.allInvites=incoming;s.a.startAutoAccept();s.respond([]);s.advance(300);
  assert.equal(s.actions().length,0);
});
test('missing native response never replays cached requests',()=>{
  const s=setup();s.context.friends_model.allInvites=incoming;s.a.startAutoAccept();s.respond(null);s.respond(undefined);s.advance(300);
  assert.equal(s.actions().length,0);
});
test('Stop cancels queued accepts and declines',()=>{
  const s=setup();s.a.startAutoAccept();s.respond([...incoming,{id:'i1',type:'FRIENDS_PLAYER_PROFILE_GAME_INVITE'},{id:'i2',type:'FRIENDS_PLAYER_PROFILE_GAME_INVITE'}]);
  assert.equal(s.actions().length,2);s.a.stopAutoAccept({silent:true});s.advance(4000);assert.equal(s.actions().length,2);
});
test('changing policy cancels actions queued under old policy',()=>{
  const s=setup();s.a.startAutoAccept();s.respond(incoming);s.a.setSettings({friendRequestMode:'ignore'});s.advance(300);assert.equal(s.actions().length,1);
});
test('Stop before delayed restore remains stopped',()=>{
  const s=setup({shift_auto_accept_enabled:'1'});s.a.stopAutoAccept({silent:true});s.advance(600);assert.equal(s.a.isRunning(),false);
});
test('AFK-owned saved state waits for current bridge approval',()=>{
  const s=setup({shift_auto_accept_enabled:'1',msbt_afk_managed:'1'});s.advance(600);assert.equal(s.a.isRunning(),false);
});
test('manual saved state resumes and outgoing requests remain untouched',()=>{
  const s=setup({shift_auto_accept_enabled:'1'});s.advance(600);assert.equal(s.a.isRunning(),true);s.respond(incoming);s.advance(300);
  assert.deepEqual(s.actions().map(c=>c[1]),['a','b']);
});
test('responses cannot create an extra polling loop in Ignore mode',()=>{
  const s=setup();s.a.setSettings({friendRequestMode:'ignore',gameInviteMode:'ignore',pollIntervalSeconds:5});
  s.a.startAutoAccept();s.respond(incoming);s.advance(4999);
  assert.equal(s.calls.filter(c=>c[0]==='FRIENDS_LOAD_REQUEST_LIST_CALL').length,1);
});
test('AFK ownership changes cancel requests queued under the old policy',()=>{
  const s=setup();s.a.setSettings({friendRequestMode:'decline'});s.a.startAutoAccept();s.respond(incoming);
  s.a.setAfkManaged(true);s.advance(300);assert.equal(s.actions().length,1);
});
for(const friend of ['accept','decline','ignore']) for(const invite of ['accept','decline','ignore']) test('manual modes '+friend+'/'+invite,()=>{
  const s=setup();s.a.setSettings({friendRequestMode:friend,gameInviteMode:invite});s.a.startAutoAccept();s.respond([{id:'f'},{id:'i',type:'FRIENDS_PLAYER_PROFILE_GAME_INVITE'}]);
  const expected=[];if(friend!=='ignore')expected.push('PLAYER_PROFILE_MENU_'+friend.toUpperCase()+'_REQUEST');
  if(invite!=='ignore')expected.push(invite==='accept'?'FRIENDS_NOTIFICATION_GAME_INVITE':'FRIENDS_NOTIFICATION_DECLINE_GAME_INVITE');
  assert.deepEqual(s.actions().map(c=>c[0]),expected);
});
test('editing protected names resets in-page review',()=>{
  const s=setup();let resets=0;s.context.window.MsbtResetProtectionReview=()=>resets++;
  s.a.setProtectedNames(['Reviewed']);assert.equal(resets,1);
});
test('bulk removal fails closed when SDK protection is unavailable',()=>{
  const s=setup(); s.context.window.ShiftMiniPanel.protectionReady=()=>false;
  s.context.friends_model.friendsList=[{id:'one',name:'Any',status:'Offline'}];
  s.a.setSettings({confirmBulkRemoval:false});
  assert.equal(s.a.confirmRemoveAllFriends().count,0);
  assert.equal(s.a.confirmRemoveAllOfflineFriends().count,0);
  s.advance(500); assert.deepEqual(s.actions(),[]);
});
test('stale before confirmation cancels removal',()=>{
  const s=setup(); let ready=true, confirm;
  s.context.window.ShiftMiniPanel.protectionReady=()=>ready;
  s.context.confirmationPopup_control={init:()=>{}};
  s.context.confirmationPopup_model={setContents:()=>{}};
  s.context.confirmationPopup_controller={ids:{popup_confirm_btn:'confirm',popup_cancel_btn:'cancel'},showConfirmationPopup:()=>{}};
  s.context.dashboard_controller={};
  s.context.$=id=>({on:(event,fn)=>{if(id==='confirm')confirm=fn;}});
  s.context.friends_model.friendsList=[{id:'one',displayName:'Any'}];
  s.a.setSettings({confirmBulkRemoval:true}); s.a.confirmRemoveAllFriends();
  ready=false; confirm(); s.advance(500); assert.deepEqual(s.actions(),[]);
});
test('stale bridge cancels pending batch',()=>{
  const s=setup(); let ready=true; s.context.window.ShiftMiniPanel.protectionReady=()=>ready;
  s.context.friends_model.friendsList=[{id:'one'}, {id:'two'}];
  s.a.setSettings({confirmBulkRemoval:false,removalBatchSize:1}); s.a.confirmRemoveAllFriends();
  ready=false; s.advance(500); assert.deepEqual(s.actions().map(c=>c[1]),['one']);
});
test('new protection skips a pending target',()=>{
  const s=setup();s.context.friends_model.friendsList=[{id:'one',displayName:'First'}, {id:'two',displayName:'Protect'}];
  s.a.setSettings({confirmBulkRemoval:false,removalBatchSize:1}); s.a.confirmRemoveAllFriends();
  s.a.setProtectedNames(['Protect']); s.advance(500); assert.deepEqual(s.actions().map(c=>c[1]),['one']);
});
test('bulk offline removal preserves protected and online friends',()=>{
  const s=setup();s.a.setProtectedNames(['KEEP']);s.a.setSettings({confirmBulkRemoval:false,removalBatchSize:2});
  s.context.friends_model.friendsList=[{id:'1',displayName:'keep',isOnline:false},{id:'2',isOnline:true},{id:'3',isOnline:false},{id:'4',info:[{service:'FRIENDS_OFFLINE'}]}];
  s.a.confirmRemoveAllOfflineFriends();s.advance(300);assert.deepEqual(s.actions().map(c=>c[1]),['3','4']);
});
console.log(`${passed} passed; ${failed} failed`);process.exitCode=failed?1:0;
