// Static proved exclusions for one finite pool. Validate before constructing
// search; never mutate rules behind a live search stack.
import assert from 'node:assert/strict';
export function verifiedGeometryCoreClass(Base,model,cores){
 assert(!model.expand&&model.complete!==false);
 const geometry=new Map(),required=new Set(model.required.map(p=>typeof p==='string'?p:p.id));
 for(const c of model.candidates){if(geometry.has(c.base))assert.deepEqual(geometry.get(c.base),c.t);else geometry.set(c.base,c.t);}
 for(const core of cores){
  assert(core.owners.length&&new Set(core.owners).size===core.owners.length&&required.has(core.point));
  const totals=new Map(),used=new Set(core.owners);
  for(const owner of used){assert(geometry.has(owner));for(const t of geometry.get(owner))totals.set(t.point,(totals.get(t.point)||0)+t.value);}
  assert([...totals.values()].every(t=>t<=model.capacity));assert((totals.get(core.point)||0)<model.capacity);
  assert(![...geometry].some(([g,t])=>!used.has(g)&&t.some(v=>v.point===core.point)&&t.every(v=>(totals.get(v.point)||0)+v.value<=model.capacity)),'Unverified geometric core');
 }
 return class GeometryCoreSearch extends Base{
  refresh(changed){this.coreOwners=new Set([...this.placed.keys()].map(id=>this.candidates.get(id).base));super.refresh(new Set(this.points.keys()));}
  reason(c){const why=super.reason(c);if(why)return why;
   if(cores.some(core=>core.owners.every(g=>g===c.base||this.coreOwners?.has(g))))return 'proved-geometric-conflict-core';return null;
  }
 };
}
