'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {createCatalogCardImages}=require('./catalog_card_images');
const row={serial:'@Uoriginal',name:'Known',image_url:'https://save-editor.be/GZO/card.png'};
test('exact GZO image works without Python or native generation',async()=>{
  let reads=0;
  const service=createCatalogCardImages({load:async()=>[row],identify:async()=>{reads++;throw Error('no Python');}});
  const result=await service.lookup([row.serial,row.serial]);
  assert.equal(result.length,1);assert.equal(result[0].image,row.image_url);assert.equal(reads,0);
});
test('equivalent encodings use GZO; different levels and case remain separate',async()=>{
  const service=createCatalogCardImages({load:async()=>[row],identify:async serials=>serials.map(s=>['@Uoriginal','@Uequivalent'].includes(s)?'same':s)});
  const result=await service.lookup(['@Uequivalent','@UotherLevel','@UOriginal']);
  assert.equal(result[0].image,row.image_url);assert.equal(result[1].image,undefined);assert.equal(result[2].image,undefined);
});
test('mixed batches preserve exact matches if semantic decoding fails',async()=>{
  const service=createCatalogCardImages({load:async()=>[row],identify:async()=>{throw Error('decoder unavailable');}});
  const result=await service.lookup(['@Uunknown',row.serial]);
  assert.equal(result[1].image,row.image_url);assert.equal(result[0].image,undefined);
});
