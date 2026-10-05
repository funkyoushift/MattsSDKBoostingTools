'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {fromNativeWidget}=require('./native_widget_card_model');
function fixture(){
  const widget={Name:'Native name',Level:'70',RarityIdent:'legendary',ItemType:'Classmod',
    ItemBaseType:'Classmod',Price:'1',RedText:'Original text',ThumbnailIcon:'missingicon',
    Visible:true,ShowLevel:true,ShowPrice:true,FirmwareVisible:false,ShowGlyphs:false};
  for(const key of ['Headline','Firmware','LegendaryStat'])widget[key]={label:'',value:'',description:'',image:'',comparison:'',ident:''};
  for(const key of ['Primary_Stat_Entries','Secondary_Stat_Entries','Tertiary_Stat_Entries','Text_Stat_Entries','Debug_Stat_Entries'])widget[key]=[];
  return widget;
}
test('invalid native artwork can produce an explicitly incomplete image without changing its data',()=>{
  const widget=fixture(),original=JSON.stringify(widget);
  assert.throws(()=>fromNativeWidget(widget),/Unmapped native card image/);
  const model=fromNativeWidget(widget,{allowMissingArtwork:true});
  assert.equal(model.thumbnailicon,'');assert.equal(model.name,widget.Name);
  assert.equal(model.redtext,widget.RedText);assert.equal(model.price,widget.Price);
  assert.deepEqual(model.artworkwarnings,['Unmapped native card image: missingicon']);
  assert.equal(JSON.stringify(widget),original);
});
test('allowing incomplete artwork does not relax required native data validation',()=>{
  const widget=fixture();delete widget.Name;
  assert.throws(()=>fromNativeWidget(widget,{allowMissingArtwork:true}),/Missing native widget field: Name/);
});
