(() => {
 const $=id=>document.getElementById(id);let busy=false;
 const message=text=>$('saveItemsPreview').textContent=text;
 function mode(){const existing=$('saveItemsMode').value==='existing';$('saveItemsExistingLabel').hidden=!existing;$('saveItemsNewLabel').hidden=existing;}
 async function run(fn){if(busy)return;busy=true;for(const id of ['saveItemsChoose','saveItemsDecode','saveItemsCommit','saveItemsCancel'])$(id).disabled=true;try{await fn();}catch(e){message(e.message);}finally{busy=false;for(const id of ['saveItemsChoose','saveItemsDecode','saveItemsCommit','saveItemsCancel'])$(id).disabled=false;}}
 $('saveItemsImportOpen').onclick=()=>{$('saveItemsImportPanel').hidden=false;$('saveItemsExisting').replaceChildren(...bookmarkGroups().map(x=>new Option(x,x)));mode();};
 $('saveItemsCancel').onclick=()=>{$('saveItemsImportPanel').hidden=true;};
 $('saveItemsMode').onchange=mode;
 async function preview(retry){$('saveItemsDestination').hidden=true;message('Reading save locally…');const result=await window.msbt.previewSaveItems({retry,account:retry?$('saveItemsAccount').value:''});if(result.canceled){message('No file selected.');return;}$('saveItemsAccountRow').hidden=!result.needsAccount;if(!result.ok){message(result.message);return;}$('saveItemsNew').value=result.suggestedFolder;message(`${result.name}${result.level?' · Level '+result.level:''}: ${result.backpack} backpack + ${result.equipped} equipped items. Lost Loot excluded.`);$('saveItemsDestination').hidden=false;}
 $('saveItemsChoose').onclick=()=>run(()=>preview(false));$('saveItemsDecode').onclick=()=>run(()=>preview(true));
 $('saveItemsCommit').onclick=()=>run(async()=>{const modeValue=$('saveItemsMode').value;const result=await window.msbt.commitSaveItems({mode:modeValue,folder:$(modeValue==='new'?'saveItemsNew':'saveItemsExisting').value,skipDuplicates:$('saveItemsSkip').checked});if(!result.ok)throw Error(result.message);await loadSerialBookmarks();openBookmarkFolder(result.destination);$('saveItemsDestination').hidden=true;message(`Imported ${result.imported} items into ${result.destination}${result.skipped?' · '+result.skipped+' duplicates skipped':''}.`);window.dispatchEvent(new Event('msbt-bookmarks-changed'));});
})();
