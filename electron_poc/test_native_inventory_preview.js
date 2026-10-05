'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {enrich}=require('./native_inventory_preview');

test('874 distinct inventory slots complete without flooding IPC and retain order',async()=>{
  const entries=Array.from({length:874},(_,i)=>({serial:'@U'+i,slot:i}));
  let active=0,peak=0,calls=0,progress=0;
  const result=await enrich(entries,async(serial,image)=>{
    assert.equal(image,false);active++;peak=Math.max(peak,active);calls++;
    await new Promise(resolve=>setImmediate(resolve));active--;
    return {ok:true,widget:{Name:serial}};
  },done=>{assert.equal(done,++progress);});
  assert.equal(calls,874);assert.ok(peak<=8);assert.equal(progress,874);
  assert.deepEqual(result.map(e=>e.serial),entries.map(e=>e.serial));
  assert.ok(result.every(e=>e.display_name===e.serial&&!e.native_preview_error));
});

test('duplicates share requests, failures do not stop later items, retry clears the error',async()=>{
  const entries=[{serial:'@UA',slot:0},{serial:'@UB',slot:1},{serial:'@UA',slot:2},{serial:'@Ua',slot:3},{}];
  const calls=[];
  const result=await enrich(entries,async serial=>{
    calls.push(serial);if(serial==='@UB')throw new Error('Unavailable');
    return {ok:true,widget:{Name:serial}};
  });
  assert.deepEqual(calls,['@UA','@UB','@Ua']);
  assert.equal(result[1].native_preview_error,'Unavailable');
  assert.equal(result[2].slot,2);assert.equal(result[3].display_name,'@Ua');
  const retry=await enrich([result[1]],async()=>({ok:true,widget:{Name:'Recovered'}}));
  assert.equal(retry[0].display_name,'Recovered');assert.equal(retry[0].native_preview_error,undefined);
  assert.equal(entries[1].native_preview_error,undefined);
});
