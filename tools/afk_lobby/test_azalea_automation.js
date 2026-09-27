// Exercise the actual rebuilt automation module with simulated native events.
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const file = process.argv[2];
const text = fs.readFileSync(file, 'utf8');
const begin = text.indexOf('var ShiftFriendAutomation = (function ()');
const end = text.indexOf('window.ShiftFriendAutomation = ShiftFriendAutomation;', begin);
assert(begin > 0 && end > begin);
const handlers = {}, calls = [], storage = new Map();
const context = {
  window: {localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},
    setTimeout:()=>1,setInterval:()=>2,clearInterval:()=>{}},
  document:{getElementById:()=>null},
  friends_model:{receivedRequestsList:[],allInvites:[]},
  friends_controller:{showSuccessMessage:()=>{},hideSuccessMessage:()=>{}},
  engine:{on:(key,fn)=>handlers[key]=fn,off:key=>delete handlers[key],call:(...args)=>calls.push(args)}
};
for (const key of ['FRIENDS_LOAD_REQUEST_LIST_RESPONSE','FRIENDS_LOAD_REQUEST_LIST_CALL',
  'FRIENDS_PLAYER_PROFILE_GAME_INVITE','PLAYER_PROFILE_MENU_ACCEPT_REQUEST',
  'PLAYER_PROFILE_MENU_DECLINE_REQUEST','FRIENDS_NOTIFICATION_DECLINE_GAME_INVITE',
  'FRIENDS_NOTIFICATION_GAME_INVITE']) context[key]=key;
vm.createContext(context);
vm.runInContext(text.slice(begin,end),context);
const a = context.ShiftFriendAutomation;
const incoming = [{id:'friend',sent:false},{id:'invite',type:context.FRIENDS_PLAYER_PROFILE_GAME_INVITE,sent:false}];
function response() { calls.length=0; handlers.FRIENDS_LOAD_REQUEST_LIST_RESPONSE(incoming); return calls.map(c=>c[0]); }
a.setSettings({friendRequestMode:'decline',gameInviteMode:'accept'});
a.startAutoAccept();
assert.deepStrictEqual(response(),['PLAYER_PROFILE_MENU_DECLINE_REQUEST','FRIENDS_NOTIFICATION_GAME_INVITE']);
const settingsBefore = JSON.stringify(a.getSettings());
a.setAfkManaged(true);
assert.deepStrictEqual(response(),['PLAYER_PROFILE_MENU_ACCEPT_REQUEST','FRIENDS_NOTIFICATION_DECLINE_GAME_INVITE']);
assert.equal(JSON.stringify(a.getSettings()), settingsBefore);
a.setSettings({friendRequestMode:'ignore',gameInviteMode:'ignore'});
assert.deepStrictEqual(response(),['PLAYER_PROFILE_MENU_ACCEPT_REQUEST','FRIENDS_NOTIFICATION_DECLINE_GAME_INVITE']);
a.setAfkManaged(false);
assert.deepStrictEqual(response(),[]);
a.stopAutoAccept({silent:true});
assert.equal(a.isRunning(),false);
assert.equal(handlers.FRIENDS_LOAD_REQUEST_LIST_RESPONSE,undefined);
console.log('PASS actual v4.4 module: manual modes, AFK override, preferences preserved, stop unregisters.');
