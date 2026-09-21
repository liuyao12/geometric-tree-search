// Saved runs have independent identities. Value equality is exact and ignores
// names, run times, array order and optional display-only reduction metadata.
export const MARKING_LIBRARY_KEY='gcts-marking-library-v1';
const labels={turtle:'Turtle',hat:'Hat',mixed:'Turtle + Hat'};
export function markingValues(model){
 const entries=model.support.map(e=>[e.tile,...e.point,e.component,e.value]).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));
 return JSON.stringify([model.setId,model.allowReflections,entries]);
}
function read(storage){
 const raw=storage?.getItem(MARKING_LIBRARY_KEY);if(!raw)return [];
 const data=JSON.parse(raw);if(data.version!==1||!Array.isArray(data.models))throw new Error('Unreadable saved marking library');
 const models=data.models.filter(model=>model.marking?.origin!=='recorded');
 if(models.length!==data.models.length)try{storage.setItem(MARKING_LIBRARY_KEY,JSON.stringify({version:1,models}));}catch{}
 return models;
}
export function savedMarkings(storage=globalThis.localStorage){try{return read(storage);}catch{return [];}}
export function rememberMarking(model,{origin='training',storage=globalThis.localStorage,now=new Date()}={}){
 if(origin==='recorded'||model.marking?.origin==='recorded')throw new Error('Only browser-trained markings can be saved');
 let models=[],readable=true;try{models=read(storage);}catch{readable=false;}
 const signature=markingValues(model),same=models.filter(m=>m.setId===model.setId&&markingValues(m)===signature);
 const existing=model.marking?.id?models.find(m=>m.marking?.id===model.marking.id):null;
 if(existing&&markingValues(existing)===signature)return {model:existing,persisted:true};
 if(!model.marking?.id&&origin!=='training'&&same.length)return {model:same.at(-1),persisted:true};
 let named=model;
 if(!model.marking?.id||existing){
  const id=crypto.randomUUID(),createdAt=now.toISOString();
  let name=origin==='legacy'?`${labels[model.setId]} · previous marking`:`${labels[model.setId]} · ${createdAt.replace('T',' ')}`;
  if(models.some(m=>m.marking?.name===name))name+=` · ${id.slice(0,6)}`;
  const prior=same.at(-1)?.marking;
  named={...model,marking:{id,name,createdAt,origin,...(prior?{sameValuesAs:{id:prior.id,name:prior.name}}:{})}};
 }
 let persisted=false;
 if(readable&&storage)try{storage.setItem(MARKING_LIBRARY_KEY,JSON.stringify({version:1,models:[...models,named]}));persisted=true;}catch{}
 return {model:named,persisted};
}
