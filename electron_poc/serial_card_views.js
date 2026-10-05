'use strict';
(() => {
  // Keep large serial lists intact and generate only previews the user opens.
  function addPreview(anchor,readCodes) {
    if(!anchor)return;
    const details=document.createElement('details'),summary=document.createElement('summary'),grid=document.createElement('div');
    details.className='serial-card-previews';summary.textContent='Item cards';
    grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px';
    details.append(summary,grid);anchor.insertAdjacentElement('afterend',details);
    let last='',timer;
    function refresh(){
      if(!details.open)return;
      const codes=[...new Set(readCodes().filter(s=>typeof s==='string'&&s.startsWith('@U')))];
      const key=JSON.stringify(codes);if(key===last)return;last=key;
      discardSavedCards(grid);grid.replaceChildren();summary.textContent=`Item cards (${codes.length})`;
      let shown=0;
      const more=document.createElement('button');more.type='button';more.textContent='Show more cards';
      function append(){
        more.remove();const end=Math.min(shown+40,codes.length);
        for(;shown<end;shown++)grid.append(savedItemCard({serial:codes[shown]}));
        if(shown<codes.length)grid.append(more);
      }
      more.addEventListener('click',append);append();
    }
    details.addEventListener('toggle',refresh);
    const update=()=>{clearTimeout(timer);timer=setTimeout(refresh,250);};
    anchor.addEventListener('input',update);anchor.addEventListener('change',update);
    anchor.addEventListener('msbt-value-changed',update);
    return refresh;
  }
  for(const id of ['boostSerialText','serialToolsSerialized','validatorBasicInput','validatorBulkInput','bl4Serial','afkCodes','afkGuaranteedCodes']){
    const field=document.getElementById(id);
    addPreview(field,()=>String(field.value||'').split(/\s+/).filter(s=>s.startsWith('@U')));
  }
})();
