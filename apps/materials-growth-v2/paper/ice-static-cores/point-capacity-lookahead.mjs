// Proved redundant finite-pool filter, not a learned marking or new scheduler.
// Reject c if, after c, an unfilled required point has no remaining inventory
// whose positive t support fits. Ignoring all markings only enlarges that set.
import assert from 'node:assert/strict';
export function capacityLookaheadClass(Base,model){
 assert(!model.expand&&model.complete!==false,'Static finite model required');
 const geometry=new Map(),at=new Map(),required=model.required.map(p=>typeof p==='string'?p:p.id);
 for(const c of model.candidates){
  assert(typeof c.base==='string');
  if(geometry.has(c.base))assert.deepEqual(geometry.get(c.base),c.t);else{
   geometry.set(c.base,c.t);for(const t of c.t){assert(Number.isSafeInteger(t.value)&&t.value>0);if(!at.has(t.point))at.set(t.point,[]);at.get(t.point).push(c.base);}
  }
 }
 return class CapacityLookahead extends Base{
  refresh(changed){this.capacityMemo=new Map();super.refresh(changed);}
  reason(c){
   const why=super.reason(c);if(why)return why;
   this.capacityMemo??=new Map();this.capacityStats??={evaluations:0,hits:0,rejections:0};
   if(this.capacityMemo.has(c.base)){this.capacityStats.hits++;return this.capacityMemo.get(c.base)!==null?'proved-future-capacity-dead':null;}
   this.capacityStats.evaluations++;
   const owners=new Set([...this.placed.keys()].map(id=>this.candidates.get(id).base));owners.add(c.base);
   const added=new Map(c.t.map(t=>[t.point,t.value]));
   const total=p=>(this.points.get(p)?.total??0)+(added.get(p)??0);
   const fits=new Map();let dead=null;
   for(const point of required)if(total(point)<this.capacity){
    const possible=(at.get(point)||[]).some(base=>{
     if(owners.has(base))return false;
     if(!fits.has(base))fits.set(base,geometry.get(base).every(t=>total(t.point)+t.value<=this.capacity));
     return fits.get(base);
    });
    if(!possible){dead=point;break;}
   }
   this.capacityMemo.set(c.base,dead);if(dead!==null){this.capacityStats.rejections++;return 'proved-future-capacity-dead';}return null;
  }
 };
}
