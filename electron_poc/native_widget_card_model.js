"use strict";

// Transport adapter for the game's final OakWidgetData_ItemCard output.
// No naming, arithmetic, rounding, filtering, sorting or fallback resolution.
const {iconUrl} = require('./native_equipment_card');
const ROWS = new Set(['headline','firmware','legendarystat']);
const ARRAYS = new Set(['primary_stat_entries','secondary_stat_entries','tertiary_stat_entries','text_stat_entries','debug_stat_entries']);

function nativeAsset(value, warnings) {
  if (typeof value !== 'string') throw new TypeError('Native image must be a string');
  if (!value) return '';
  const url=iconUrl(value);
  if (!url) {
    if (!warnings) throw new Error('Unmapped native card image: '+value);
    warnings.push('Unmapped native card image: '+value);
    return ''; // Explicitly incomplete artwork; never invent a replacement icon.
  }
  return url;
}
function row(value, warnings) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError('Missing native stat row');
  for (const key of ['label','value','description','image','comparison','ident'])
    if (typeof value[key] !== 'string') throw new TypeError('Missing native row field: '+key);
  return {loc_text:value.label,value:value.value,description:value.description,
    image:nativeAsset(value.image,warnings),comparison:value.comparison,ident:value.ident,
    idx:value.index,priority:value.priority};
}
function fromNativeWidget(widget, {allowMissingArtwork=false}={}) {
  if (!widget || typeof widget !== 'object' || Array.isArray(widget)) throw new TypeError('Missing native widget');
  // All of these values are supplied by the native consumer. Reject partial
  // model exports rather than silently routing them through the old resolver.
  for (const key of ['Name','Level','RarityIdent','ItemType','ItemBaseType','Price','RedText','ThumbnailIcon'])
    if (typeof widget[key] !== 'string') throw new TypeError('Missing native widget field: '+key);
  for (const key of ['Visible','ShowLevel','ShowPrice','FirmwareVisible','ShowGlyphs'])
    if (typeof widget[key] !== 'boolean') throw new TypeError('Missing native widget flag: '+key);
  const model={}, warnings=allowMissingArtwork?[]:undefined;
  for (const [key,value] of Object.entries(widget)) {
    const name=key.toLowerCase(); // Reflected ASCII property names only.
    if (ROWS.has(name)) model[name]=row(value,warnings);
    else if (ARRAYS.has(name)) {
      if (!Array.isArray(value)) throw new TypeError('Missing native stat array: '+key);
      model[name]=value.map(value=>row(value,warnings));
    } else if (name==='thumbnailicon') model[name]=nativeAsset(value,warnings);
    else if (name==='glyphs') {
      if (widget.ShowGlyphs) throw new Error('Native glyph export has not been implemented');
      model[name]=[]; // Hidden input prompts are outside standalone card images.
    } else if (value===null || typeof value==='object' || typeof value==='number'&&!Number.isFinite(value)) {
      throw new TypeError('Unresolved native widget field: '+key);
    } else model[name]=value;
  }
  for (const field of [...ROWS,...ARRAYS])
    if (!(field in model)) throw new TypeError('Missing native widget field: '+field);
  if(warnings?.length)model.artworkwarnings=warnings;
  return model;
}
module.exports={fromNativeWidget};
