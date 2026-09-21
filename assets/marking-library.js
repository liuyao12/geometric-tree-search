// Saved runs have independent identities. Value equality is exact and ignores
// names, run times, array order and display-only reduction metadata.
import {markingMetadata} from './marking-metadata.js?v=20260921-domain-names';
export const MARKING_LIBRARY_KEY='gcts-marking-library-v1';
export const markingDomain=model=>`${model.setId}:${model.lattice??'A2'}`;
function shortTimestamp(model){
 const date=new Date(model.marking?.createdAt),pad=n=>String(n).padStart(2,'0');
 return Number.isNaN(date.getTime())?'Previous':`${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
export function markingName(model){
 const {points,values}=markingMetadata(model),run=model.marking?.runNumber??1;
 return `${shortTimestamp(model)}${run>1?` #${run}`:''} · ${points} points · ${values} values`;
}
function nameRuns(models){
 const counts=new Map();
 const named=models.map(model=>{const key=`${markingDomain(model)}:${shortTimestamp(model)}`,runNumber=(counts.get(key)??0)+1;counts.set(key,runNumber);const named={...model,marking:{...model.marking,runNumber}};named.marking.name=markingName(named);return named;});
 const byId=new Map(named.map(model=>[model.marking.id,model]));
 for(const model of named){const prior=byId.get(model.marking.sameValuesAs?.id);if(prior){if(markingDomain(prior)!==markingDomain(model))delete model.marking.sameValuesAs;else model.marking.sameValuesAs={id:prior.marking.id,name:prior.marking.name};}}
 return named;
}
export function markingValues(model){
 const entries=model.support.map(e=>[e.tile,...e.point,e.component,e.value]).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));
 return JSON.stringify([markingDomain(model),model.allowReflections,entries]);
}
function read(storage){
 const raw=storage?.getItem(MARKING_LIBRARY_KEY);if(!raw)return [];
 const data=JSON.parse(raw);if(data.version!==1||!Array.isArray(data.models))throw new Error('Unreadable saved marking library');
 const models=data.models.filter(model=>model.marking?.origin!=='recorded');
 if(models.length!==data.models.length)try{storage.setItem(MARKING_LIBRARY_KEY,JSON.stringify({version:1,models}));}catch{}
 return nameRuns(models);
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
  const prior=same.at(-1)?.marking;
  named={...model,marking:{id,createdAt,origin,...(prior?{sameValuesAs:{id:prior.id,name:prior.name}}:{})}};
 }
 named=nameRuns([...models,named]).at(-1);
 let persisted=false;
 if(readable&&storage)try{storage.setItem(MARKING_LIBRARY_KEY,JSON.stringify({version:1,models:[...models,named]}));persisted=true;}catch{}
 return {model:named,persisted};
}
