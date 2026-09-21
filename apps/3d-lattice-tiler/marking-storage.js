export const STORAGE_KEY='gcts-3d-markings-v1';
export function remember3DMarking(model,marking,storage=globalThis.localStorage){
 if(!marking?.accepted)return marking;
 if(marking.saved)return marking;
 const now=new Date(),pad=n=>String(n).padStart(2,'0'),name=`${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())} · ${marking.points} points · ${marking.values} values`;
 const saved={...marking,saved:{id:globalThis.crypto.randomUUID(),name,createdAt:now.toISOString(),persisted:false}};
 const domain={capacity:model.capacity,allowReflections:!!model.allowReflections,placementDomain:model.placementDomain??null,orientations:model.orientations.map(o=>({type:o.type,index:o.index,cells:o.cells})),extent:marking.extent};
 try{const raw=storage.getItem(STORAGE_KEY),library=raw?JSON.parse(raw):[];if(!Array.isArray(library))throw Error('Unreadable history');saved.saved.persisted=true;storage.setItem(STORAGE_KEY,JSON.stringify([...library,{domain,marking:saved}]));}catch{saved.saved.persisted=false;}
 return saved;
}
