'use strict';
const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const source=readFileSync(require('node:path').join(__dirname,'renderer.js'),'utf8');
const slice=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
let generated=['@Ufirst'], sent=[];
const context={state:{confirmedSerial:'',editorStagedSerial:''},els:{serialInput:{value:''},editorSerialCopies:{}},
 getValue:node=>node.value.trim(),collectEditorSerials:()=>generated,
 updateSerialState(){if(context.state.confirmedSerial!==context.els.serialInput.value)context.state.confirmedSerial='';},
 serialValidationMessage:value=>value.startsWith('@U')?'':'invalid',setLine(){},setOutput(){},getInt:()=>1,
 sendSerialPayload:async(_mode,serial)=>sent.push(serial)};
vm.createContext(context);
vm.runInContext(slice('async function sendEditorSerial(mode)', 'async function sendBoostSerial(mode)'),context);
(async()=>{
 await context.sendEditorSerial('self');
 generated=['@Usecond'];await context.sendEditorSerial('self');
 assert.deepEqual(sent,['@Ufirst','@Usecond']);
 generated=[];await context.sendEditorSerial('self');assert.equal(sent.length,2);
 generated=['@Uthird','@Ufourth'];await context.sendEditorSerial('self');assert.equal(sent.length,2);
 context.els.serialInput.value='@Umanual';await context.sendEditorSerial('self');assert.equal(sent.at(-1),'@Umanual');
 console.log('Editor sender: sequential codes, missing/ambiguous output, and manual override passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
