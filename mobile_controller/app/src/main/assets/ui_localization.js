/* Offline UI localization. Translate app-owned text, never user/game data or values. */
(() => {
  'use strict';
  const catalog=window.MsbtLanguageCatalog||{};
  const textState=new WeakMap(),attributeState=new WeakMap();
  const normalize=s=>String(s).replace(/\s+/g,' ').trim();
  const skip='script,style,pre,code,iframe,[contenteditable="true"],[data-i18n-skip],[data-language-selector],.bl4-item-card,.saved-item-card,.bookmark-row,.saved-folder-nav,#communityResults,#communityPreviewItems,#communityPreviewTitle,#communityPreviewDescription,#invEquippedGrid,#invBackpackGrid,#bl4CatalogGrid,#afkLog,.bl4-code-card,#quickMenuSlotGrid,#devMyFavoriteRows,#travelFavoriteRows,#hoardWaveList';
  const dataSelect=/^(targetSelect|boostSpawnAnchor|boostSerialTargetSelect|bookmarkTargetSelect|invTargetSelect|invGiveTargetSelect|afkBookmarkFolder|afkBookmarks|bookmarkFolderPath|bookmarkGroupFilter|bookmarkGroup|communitySubmitFolder|saveItemsExisting|bl4CreatorFilter|locationBookmarkList|travelMapList|travelStationList|itempoolList|hoardActorList|challengeListSelect)$/;
  function excluded(el){
    if(!el||el.closest(skip))return true;
    const select=el.closest('select');
    return !!select&&dataSelect.test(select.id);
  }
  function language(){return window.msbtI18n?.language||'en';}
  const countFormats=[
    [/^(\d[\d,.]*) selected$/,['{1} selected','{1} seleccionados','{1} sélectionnés','{1} selecionados','{1} ausgewählt','{1} geselecteerd']],
    [/^(\d+) \/ (\d+) selected$/,['{1} / {2} selected','{1} / {2} seleccionados','{1} / {2} sélectionnés','{1} / {2} selecionados','{1} / {2} ausgewählt','{1} / {2} geselecteerd']],
    [/^(\d+) shown \/ (\d+) saved \/ (\d+) selected$/,['{1} shown / {2} saved / {3} selected','{1} mostrados / {2} guardados / {3} seleccionados','{1} affichés / {2} enregistrés / {3} sélectionnés','{1} exibidos / {2} salvos / {3} selecionados','{1} angezeigt / {2} gespeichert / {3} ausgewählt','{1} getoond / {2} opgeslagen / {3} geselecteerd']],
    [/^(\d+) item\(s\) selected · (Community library|My saved items)$/,['{1} item(s) selected · {2}','{1} objetos seleccionados · {2}','{1} objets sélectionnés · {2}','{1} itens selecionados · {2}','{1} Gegenstände ausgewählt · {2}','{1} voorwerpen geselecteerd · {2}']],
    [/^Page (\d+) \/ (\d+)$/,['Page {1} / {2}','Página {1} / {2}','Page {1} / {2}','Página {1} / {2}','Seite {1} / {2}','Pagina {1} / {2}']]
  ];
  const templates=Object.keys(catalog).filter(key=>/\{\d+\}/.test(key)).sort((a,b)=>b.replace(/\{\d+\}/g,'').length-a.replace(/\{\d+\}/g,'').length).map(key=>{
    const indices=[];
    const pattern=key.split(/(\{\d+\})/).map(part=>{
      if(/^\{\d+\}$/.test(part)){indices.push(part.slice(1,-1));return '(.*?)';}
      return part.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    }).join('');
    return {key,indices,pattern:new RegExp('^'+pattern+'$')};
  });
  function translated(source){
    if(Object.hasOwn(catalog,source))return lookup(source);
    for(const [pattern,values]of countFormats){const match=source.match(pattern);if(match)return values[window.msbtI18n.locales.indexOf(language())].replace(/\{(\d+)\}/g,(_,i)=>lookup(match[Number(i)]));}
    for(const template of templates){const match=source.match(template.pattern);if(match){const values={};template.indices.forEach((id,i)=>{values[id]=match[i+1];});return lookup(template.key).replace(/\{(\d+)\}/g,(_,id)=>values[id]);}}
    return source;
  }
  function originalText(node){
    if(node.nodeType===Node.TEXT_NODE){const r=textState.get(node);return r&&node.nodeValue===r.output?r.source:node.nodeValue;}
    return [...node.childNodes].map(originalText).join('');
  }
  function lookup(source){return language()==='en'?source:(catalog[source]?.[language()]||source);}
  function renderText(node){
    const el=node.parentElement;if(excluded(el)||el.closest('[data-i18n]'))return;
    const now=node.nodeValue;
    let record=textState.get(node);
    // A later status/label update replaces the previous source instead of being overwritten.
    if(!record||now!==record.output){record={source:now,output:now};textState.set(node,record);}
    const key=normalize(record.source);
    const leading=record.source.match(/^\s*/)[0],trailing=record.source.match(/\s*$/)[0];
    const result=leading+translated(key)+trailing;
    record.output=result;if(now!==result)node.nodeValue=result;
  }
  function renderAttributes(el){
    if(excluded(el))return;
    let states=attributeState.get(el);if(!states){states={};attributeState.set(el,states);}
    for(const attr of ['title','placeholder','aria-label']){
      if(!el.hasAttribute(attr))continue;
      const now=el.getAttribute(attr);let record=states[attr];
      if(!record||now!==record.output)record=states[attr]={source:now,output:now};
      const key=normalize(record.source);if(!Object.hasOwn(catalog,key))continue;
      record.output=lookup(key);if(now!==record.output)el.setAttribute(attr,record.output);
    }
  }
  function visit(root){
    if(root.nodeType===Node.TEXT_NODE){renderText(root);return;}
    if(root.nodeType!==Node.ELEMENT_NODE||excluded(root))return;
    // Input values are protected; placeholder/accessible labels are interface text.
    renderAttributes(root);
    for(const child of root.childNodes){
      if(child.nodeType===Node.ELEMENT_NODE&&child.matches('input,textarea')){
        for(const attr of ['placeholder','aria-label','title']){
          if(!child.hasAttribute(attr))continue;
          let states=attributeState.get(child);if(!states){states={};attributeState.set(child,states);}
          const now=child.getAttribute(attr);let record=states[attr];
          if(!record||now!==record.output)record=states[attr]={source:now,output:now};
          const key=normalize(record.source);if(Object.hasOwn(catalog,key)){record.output=lookup(key);if(now!==record.output)child.setAttribute(attr,record.output);}
        }
      }else visit(child);
    }
  }
  const observer=new MutationObserver(records=>{
    observer.disconnect();
    try{for(const r of records){if(r.type==='childList')r.addedNodes.forEach(visit);else if(r.type==='characterData')renderText(r.target);else renderAttributes(r.target);}}
    finally{observe();}
  });
  function observe(){observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','placeholder','aria-label']});}
  function apply(){observer.disconnect();try{visit(document.body);}finally{observe();}}
  window.MsbtTranslateUi={apply,text:source=>translated(normalize(source)),originalText,catalog};
  window.addEventListener('msbt-language-change',apply);
  apply();
})();
