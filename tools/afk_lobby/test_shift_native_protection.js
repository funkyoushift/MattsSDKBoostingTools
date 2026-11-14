'use strict';
// node test_shift_native_protection.js <repaired dashboard_controller.js> <repaired dashboard.html>
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2], 'utf8');
const html = fs.readFileSync(process.argv[3], 'utf8');
const marker = '// Native Friends protection uses the same mutable list and explicit Save guard.';
assert(source.includes(marker));

function methodAt(marker, shorthand=false) {
  const start = source.indexOf(marker);
  assert(start >= 0, marker);
  const fn = shorthand ? start : source.indexOf('function', start);
  const open = source.indexOf('{', fn);
  let depth = 1;
  for (let i = open + 1; i < source.length; i++) {
    if (source[i] === '{') depth++;
    if (source[i] === '}' && --depth === 0) return (shorthand?'function ':'')+source.slice(fn, i + 1);
  }
  throw Error('Unterminated method');
}

let names = ['Existing'], opened = 0, changed = 0, writes = 0, socialCalls = 0;
const feedback = {nodes:[], get firstChild(){return this.nodes[0];}, removeChild(){this.nodes.shift();}, appendChild(n){this.nodes.push(n);}};
const search = {value:'unrelated'};
const ctx = {
  window:{}, SHIFT_SERVICE:'shift',
  friends_model:{selectedPlayer:{id:'friend-id',shiftName:'stale wrong name',info:[{service:'steam',text:'Platform alias'},{service:'shift',text:'  ExactSHIFTName  '}]},updateModel(){}},
  document:{getElementById:id=>id==='shift_settings_protected_feedback'?feedback:id==='shift_settings_protected_search'?search:null,createTextNode:text=>({text})},
  engine:{call(){socialCalls++;}},
  $:node=>({attr:()=>node.action}),
  Array, String, JSON,
};
ctx.window.ShiftFriendAutomation = {
  getProtectedNames:()=>names.slice(),
  addProtectedName(name){if(names.some(n=>n.toLowerCase()===name.toLowerCase()))return false;names.push(name);ctx.window.MsbtProtectionDirty=true;ctx.window.MsbtProtectionReviewed=false;return true;},
};
ctx.window.ShiftMiniPanel = {
  openProtectedList(){opened++;}, filterProtected(q){assert.equal(q,'');},
  notifySettingsChanged(){changed++;}, saveSettingsNow(){writes++;},
};
vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf(marker)), ctx);
vm.runInContext('friends_model.setPlayerProfileActions = '+methodAt('    setPlayerProfileActions: function'),ctx);
ctx.friends_model.setPlayerProfileActions([{id:'removeFriendActionId',display:'Remove',disabled:false}]);
assert.equal(ctx.friends_model.playerProfileActions[0].id,'msbtProtectPlayerActionId');
assert.equal(ctx.friends_model.playerProfileActions[1].id,'removeFriendActionId');
vm.runInContext('onClick = '+methodAt('            onClickAction: function'),ctx);
ctx.onClick.call({action:'msbtProtectPlayerActionId'});
assert.deepEqual(names,['Existing','ExactSHIFTName']);
assert.equal(opened,1);assert.equal(changed,1);assert.equal(search.value,'');
assert.equal(ctx.window.MsbtProtectionDirty,true);assert.equal(ctx.window.MsbtProtectionReviewed,false);
assert.match(feedback.nodes[0].text,/Review the list, then choose Save protected list/);
assert.equal(writes,0);assert.equal(socialCalls,0);
console.log('PASS native profile model and dispatch select SHiFT identity, stage protection and preserve explicit Save');

ctx.friends_model.setPlayerProfileActions([]);
assert.equal(ctx.friends_model.playerProfileActions[0].display,'Protected player - view list');
ctx.friends_model.reportActionsList=[{id:'reportReasonId',display:'Report reason'}];
ctx.friends_model.setPlayerProfileActions(ctx.friends_model.reportActionsList);
assert.equal(ctx.friends_model.playerProfileActions.length,1,'report reasons must not gain a protection action');
ctx.friends_model.selectedPlayer.info[1].text='exactshiftname';
ctx.onClick.call({action:'msbtProtectPlayerActionId'});
assert.equal(names.length,2);assert.equal(changed,1);assert.match(feedback.nodes[0].text,/Already protected/);
ctx.friends_model.selectedPlayer={shiftName:'STALE',info:[{service:'steam',text:'Platform only'}]};
ctx.friends_model.setPlayerProfileActions([{id:'viewProfileId'}]);
assert.equal(ctx.friends_model.playerProfileActions.length,1);
ctx.onClick.call({action:'msbtProtectPlayerActionId'});
assert.equal(names.length,2);assert.equal(opened,2);assert.equal(socialCalls,0);
console.log('PASS duplicate names and platform-only/stale SHiFT identity do not add incorrect protection');

const friends = html.indexOf('<div id="friends_container"');
const panel = html.indexOf('id="msbt_native_protection_panel"');
assert(panel > friends);
for (const id of ['shift_settings_protected_add_input','shift_settings_protected_search','shift_settings_protected_list','shift_settings_storage_status']) {
  assert.equal(html.split('id="'+id+'"').length-1,1,id+' must be unique');
  assert(html.indexOf('id="'+id+'"')>panel,id+' must live in native Friends');
}
assert(html.includes('id="friends_protected_list_btn"'));
assert(html.includes('id="friends_protected_list_btn_two_col"'));
assert(html.includes('id="msbt_native_protection_save"'));
assert(source.includes('if (window.ShiftMiniPanel && window.ShiftMiniPanel.handleProtectedListPad(btnAction)) return;'));
console.log('PASS one editor lives in native Friends with header entry points, Save and guarded input routing');

let nativeClicks=0, friendsHidden=false;
const buttons=Array.from({length:3},()=>({className:'button',click(){nativeClicks++;}}));
const nativePanel={style:{display:'block'},querySelectorAll:()=>buttons};
ctx.byId=id=>id==='msbt_native_protection_panel'?nativePanel:null;
ctx.$=()=>({hasClass:()=>friendsHidden});
ctx.PadKeys={A:'a',B:'b',Up:'up',Down:'down',X:'x'};
ctx.Keys={FEnter:'enter'};
vm.runInContext('var nativeProtectionFocus=0;'+['closeProtectedList','nativeProtectionActions','focusNativeProtection','handleProtectedListPad'].map(name=>methodAt('    function '+name+'(')).join('\n'),ctx);
assert.equal(ctx.handleProtectedListPad('x'),true,'side-menu shortcut must be swallowed');
ctx.handleProtectedListPad('down');
assert.match(buttons[1].className,/msbt-protection-focused/);
ctx.handleProtectedListPad('a');assert.equal(nativeClicks,1);
ctx.document.activeElement={tagName:'INPUT'};
ctx.handleProtectedListPad('enter');assert.equal(nativeClicks,1,'typing Enter must not trigger a second focused action');
ctx.handleProtectedListPad('b');assert.equal(nativePanel.style.display,'none');
assert.equal(ctx.handleProtectedListPad('a'),false,'closing restores native input routing');
nativePanel.style.display='block';friendsHidden=true;
assert.equal(ctx.handleProtectedListPad('a'),false,'a hidden Friends page cannot capture another screen');
console.log('PASS controller navigation, close and text entry prevent hidden profile actions without trapping other screens');

let now=1000, underlyingInputs=0, scrolledIntoView=0;
friendsHidden=false;nativePanel.style.display='block';ctx.document.activeElement=null;
ctx.Date={now:()=>now};ctx.GET_CONTROLLER_TYPE='controllerType';
ctx.engine.call=()=>({then(){}});
ctx.dashboard_control={isButtonHeld:false,gamepadHasScrolled:false,gamepadScrollInterval:100,updateInputTypeIcons(){}};
ctx.dashboard_controller={currentController:{handlePad(){underlyingInputs++;}}};
ctx.window.ShiftMiniPanel.handleProtectedListPad=ctx.handleProtectedListPad;
for (const name of ['handleButtonHeld','handleButtonRelease']) {
  vm.runInContext('dashboard_control.'+name+'='+methodAt(name+'(btnAction, isKeyboard)',true),ctx);
}
vm.runInContext('dashboard_control.handlePad='+methodAt('        handlePad: function (btnAction, isReleased)'),ctx);
vm.runInContext('nativeProtectionFocus=0',ctx);
ctx.dashboard_control.handlePad('down',false);
now+=200;ctx.dashboard_control.handlePad('down',false);
assert.equal(vm.runInContext('nativeProtectionFocus',ctx),1);
ctx.dashboard_control.handlePad('down',true);
assert.equal(vm.runInContext('nativeProtectionFocus',ctx),1,'held Down must not add another step on release');
assert.equal(ctx.dashboard_control.gamepadHasScrolled,false);
assert.equal(ctx.dashboard_control.isButtonHeld,false);
assert.equal(ctx.dashboard_control.buttonPressStartTime,0);
ctx.dashboard_control.handlePad('b',false);
now+=2000;ctx.dashboard_control.handlePad('b',false);
assert.equal(nativePanel.style.display,'block','B hold must not close the page or touch native holding CSS');
ctx.dashboard_control.handlePad('b',true);
assert.equal(nativePanel.style.display,'none');
assert.equal(ctx.dashboard_control.isButtonHeld,false);
assert.equal(underlyingInputs,0);
console.log('PASS real dashboard held/released routing repeats once, resets state and consumes B before native hold mutations');

const opening=[];
ctx.closeSettings=()=>opening.push('closeSettings');
ctx.loadSettingsIntoControls=()=>opening.push('load');
ctx.ensureProtectionReview=()=>opening.push('review');
ctx.renderProtectedNames=()=>{};ctx.renderSettingsProtectedNames=()=>{};
ctx.currentStorageMode='session';
buttons[0].scrollIntoView=()=>{scrolledIntoView++;assert(opening.includes('review'));};
vm.runInContext(methodAt('    function openProtectedList('),ctx);
ctx.openProtectedList();
assert.deepEqual(opening,['closeSettings','load','review']);
assert.equal(nativePanel.style.display,'block');assert.equal(scrolledIntoView,1);
assert.match(html, /id="msbt_native_protection_save"[^>]*onclick="return window.ShiftMiniPanel.saveSettingsNow\(\);"/);
vm.runInContext(methodAt('    function openSettings('),ctx);
ctx.openSettings();assert.equal(nativePanel.style.display,'none');
console.log('PASS opening creates the review control before focus; Save uses the existing guard and Customize closes the editor');
