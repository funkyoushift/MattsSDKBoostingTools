'use strict';
const assert=require('node:assert/strict');
const {gzoImageIndex,resolveImageRequests}=require('./item_image_priority');
const serial='@UknownCaseSensitive';
const image='https://save-editor.be/GZO/images/test.webp';
const images=gzoImageIndex([{serial,image_url:image,name:'Catalog title'},
  {serial:'@Ubad',image_url:'https://evil.example/GZO/image.webp'}]);
let lookups=0,demands=0;
const cache={lookup:()=>{lookups++;return {state:'missing'};},demand:()=>{demands++;return {state:'queued'};}};
for(const operation of ['lookup','demand']){
  const rows=resolveImageRequests(Array(500).fill(serial),images,cache,operation,0);
  assert(rows.every(r=>r.source==='gzo'&&r.image===image&&r.itemCard.name==='Catalog title'));
}
assert.equal(lookups,0);assert.equal(demands,0);
assert.equal(resolveImageRequests([serial.toLowerCase()],images,cache,'lookup',0)[0].state,'missing');
assert.equal(resolveImageRequests(['@Unew'],images,cache,'demand',0)[0].state,'queued');
assert.equal(lookups,1);assert.equal(demands,1);assert.equal(images.size,1);
const keys=new Map([[serial,'parts1'],['@Ucompact','parts1'],['@Ufirst','parts2'],['@UsameParts','parts2']]);
const equivalents=new Map([['parts1',images.get(serial)]]),representatives=new Map();
const compact=resolveImageRequests(['@Ucompact'],images,cache,'demand',0,keys,equivalents,representatives)[0];
assert.equal(compact.source,'gzo');assert.equal(compact.match,'equivalent');assert.equal(demands,1);
const calls=[],dedupCache={demand:s=>{calls.push(s);return {state:'queued'};},lookup:s=>({state:'ready',originalSerial:s})};
resolveImageRequests(['@Ufirst','@UsameParts'],images,dedupCache,'demand',0,keys,equivalents,representatives);
assert.deepEqual(calls,['@Ufirst','@Ufirst']);
assert.equal(resolveImageRequests(['@UsameParts'],images,dedupCache,'lookup',0,keys,equivalents,representatives)[0].originalSerial,'@Ufirst');
console.log('GZO priority: 1,000 known-code resolutions made zero NCS cache or submission calls; case-sensitive misses preserved.');
