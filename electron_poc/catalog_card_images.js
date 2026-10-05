'use strict';
const {gzoImageIndex}=require('./item_image_priority');
function createCatalogCardImages({load,identify}) {
  let indexPromise=null;
  const identities=new Map();
  async function keys(serials) {
    const missing=[...new Set(serials)].filter(s=>!identities.has(s));
    if(missing.length){
      const values=await identify(missing);
      if(!Array.isArray(values)||values.length!==missing.length)throw new Error('Serial identity unavailable');
      missing.forEach((serial,i)=>identities.set(serial,values[i]));
    }
  }
  async function index() {
    if(!indexPromise) indexPromise=(async()=>{
      const exact=gzoImageIndex(await load());
      const equivalent=new Map();
      return {exact,equivalent,ready:null};
    })().catch(error=>{indexPromise=null;throw error;});
    return indexPromise;
  }
  return {
    async lookup(serials){
      const valid=[...new Set(serials)].filter(s=>typeof s==='string'&&s.startsWith('@U')&&s.length<=8192);
      const images=await index();
      const missing=valid.filter(serial=>!images.exact.has(serial));
      if(missing.length){
        if(!images.ready)images.ready=(async()=>{
          await keys([...images.exact.keys()]);
          for(const [serial,image] of images.exact){const key=identities.get(serial);if(key&&!images.equivalent.has(key))images.equivalent.set(key,image);}
        })().catch(error=>{images.ready=null;throw error;});
        try{await images.ready;await keys(missing);}catch{/* Exact images still work when the decoder is unavailable. */}
      }
      return valid.map(serial=>({serial,...(images.exact.get(serial)||images.equivalent.get(identities.get(serial))||{})}));
    },
    reset(){indexPromise=null;identities.clear();}
  };
}
module.exports={createCatalogCardImages};
