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
    if(document.documentElement.dataset.msbtLanguageSurface==='editor'&&el.closest('select option:not([data-i18n-ui]),.part-name,.item-name,.part-code,.serial-code,#mi_fileList,#fileList,#mi_itemPartsBreakdownAdvanced,#itemPartsBreakdownAdvanced'))return true;
    const select=el.closest('select');
    const option=el.closest('option');
    return !!select&&dataSelect.test(select.id)&&!!option&&option.value!==''&&!option.hasAttribute('data-i18n-ui');
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
    // Encoded examples and identifiers are data even when used as placeholders.
    if(/@U[A-Za-z0-9$!%&/)]{6,}/.test(source))return source;
    if(Object.hasOwn(catalog,source))return lookup(source);
    for(const [pattern,values]of countFormats){const match=source.match(pattern);if(match)return (values[window.msbtI18n.locales.indexOf(language())]||values[0]).replace(/\{(\d+)\}/g,(_,i)=>lookup(match[Number(i)]));}
    for(const template of templates){const match=source.match(template.pattern);if(match){const values={};template.indices.forEach((id,i)=>{values[id]=match[i+1];});return lookup(template.key).replace(/\{(\d+)\}/g,(_,id)=>values[id]);}}
    return source;
  }
  function originalText(node){
    if(node.nodeType===Node.TEXT_NODE){const r=textState.get(node);return r&&node.nodeValue===r.output?r.source:node.nodeValue;}
    return [...node.childNodes].map(originalText).join('');
  }
  function lookup(source){return language()==='en'?source:(catalog[source]?.[language()]||source);}
  // Read-only maintenance inventory uses the same data exclusions as rendering.
  function audit(root=document.body){
    const found=new Map();
    function add(value){
      const source=normalize(value);
      if(!/[A-Za-z]{2}/.test(source)||/^\d+[\d/.,: ]+(AM|PM)$/.test(source)||/@U[A-Za-z0-9$!%&/)]{6,}/.test(source))return;
      const key=Object.hasOwn(catalog,source)?source:templates.find(t=>t.pattern.test(source))?.key;
      found.set(source,{source,key:key||null});
    }
    function scan(node){
      if(node.nodeType===Node.TEXT_NODE){
        if(!excluded(node.parentElement)&&!node.parentElement.closest('[data-i18n]'))add(originalText(node));
        return;
      }
      if(node.nodeType!==Node.ELEMENT_NODE||excluded(node))return;
      for(const attr of ['title','placeholder','aria-label'])if(node.hasAttribute(attr)){
        const saved=attributeState.get(node)?.[attr];
        add(saved&&node.getAttribute(attr)===saved.output?saved.source:node.getAttribute(attr));
      }
      if(!node.matches('input,textarea'))node.childNodes.forEach(scan);
    }
    scan(root);return [...found.values()];
  }
  function renderText(node){
    const el=node.parentElement;if(excluded(el)||el.closest('[data-i18n]'))return;
    const now=node.nodeValue;
    let record=textState.get(node);
    // A later status/label update replaces the previous source instead of being overwritten.
    if(!record||now!==record.output){record={source:now,output:now};textState.set(node,record);}
    const key=normalize(record.source);
    const leading=record.source.match(/^\s*/)[0],trailing=record.source.match(/\s*$/)[0];
    const output=translated(key);
    const result=output===key?record.source:leading+output+trailing;
    record.output=result;if(now!==result)node.nodeValue=result;
  }
  function renderAttributes(el){
    if(excluded(el))return;
    let states=attributeState.get(el);if(!states){states={};attributeState.set(el,states);}
    for(const attr of ['title','placeholder','aria-label']){
      if(!el.hasAttribute(attr))continue;
      const now=el.getAttribute(attr);let record=states[attr];
      if(!record||now!==record.output)record=states[attr]={source:now,output:now};
      const key=normalize(record.source);
      const output=translated(key);record.output=output===key?record.source:output;
      if(now!==record.output)el.setAttribute(attr,record.output);
    }
  }
  function visit(root){
    if(root.nodeType===Node.TEXT_NODE){renderText(root);return;}
    if(root.nodeType!==Node.ELEMENT_NODE||excluded(root))return;
    // Input values are protected; placeholder/accessible labels are interface text.
    renderAttributes(root);
    if(root.matches('input,textarea'))return;
    for(const child of root.childNodes){
      visit(child);
    }
  }
  const observer=new MutationObserver(records=>{
    observer.disconnect();
    try{for(const r of records){if(r.type==='childList')r.addedNodes.forEach(visit);else if(r.type==='characterData')renderText(r.target);else renderAttributes(r.target);}}
    finally{observe();}
  });
  function observe(){observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','placeholder','aria-label']});}
  function apply(){observer.disconnect();try{visit(document.body);}finally{observe();}}
  window.MsbtTranslateUi={apply,text:source=>translated(normalize(source)),originalText,catalog,audit};
  window.addEventListener('msbt-language-change',apply);
  apply();
})();
