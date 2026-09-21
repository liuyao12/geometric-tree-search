export const STORAGE_KEY='gcts-3d-markings-v1';
// Target size and search budget are not part of a tile-and-lattice system.
export function markingSystem(model){
 return {capacity:model.capacity,allowReflections:!!model.allowReflections,placementDomain:model.placementDomain??null,orientations:model.orientations.map(o=>({type:o.type,index:o.index,cells:o.cells}))};
}
export function matching3DMarkings(model,storage){
 try{storage??=globalThis.localStorage;const library=JSON.parse(storage.getItem(STORAGE_KEY)??'[]');if(!Array.isArray(library))return [];
  const system=JSON.stringify(markingSystem(model));return library.filter(entry=>{try{return entry?.marking?.accepted&&entry.marking.saved?.id&&JSON.stringify(markingSystem(entry.domain))===system;}catch{return false;}});
 }catch{return [];}
}
export function remember3DMarking(model,marking,storage){
 if(!marking?.accepted)return marking;
 if(marking.saved)return marking;
 const now=new Date(),pad=n=>String(n).padStart(2,'0'),name=`${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())} · ${marking.points} points · ${marking.values} values`;
 const saved={...marking,saved:{id:globalThis.crypto.randomUUID(),name,createdAt:now.toISOString(),persisted:false}};
 const domain={...markingSystem(model),extent:marking.extent};
 try{storage??=globalThis.localStorage;const raw=storage.getItem(STORAGE_KEY),library=raw?JSON.parse(raw):[];if(!Array.isArray(library))throw Error('Unreadable history');const usedNames=new Set(library.map(e=>e?.marking?.saved?.name));let n=2;while(usedNames.has(saved.saved.name))saved.saved.name=name+' · run '+n++;saved.saved.persisted=true;storage.setItem(STORAGE_KEY,JSON.stringify([...library,{domain,marking:saved}]));}catch{saved.saved.persisted=false;}
 return saved;
}
