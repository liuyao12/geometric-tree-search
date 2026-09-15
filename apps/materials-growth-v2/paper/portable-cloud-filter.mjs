// Set-valued geometric markings on a fixed registered candidate universe.
// Pair-disjointness is a necessary rejection test. Completion additionally
// requires a verified common cloud, not merely pairwise compatibility.
import assert from 'node:assert/strict';
const color=c=>JSON.stringify(c),distance=(a,b)=>Math.hypot(...a.map((x,i)=>x-b[i]));
export function cloudContains(a,b,radius){
 assert(Number.isFinite(radius)&&radius>=0);
 assert(a.vectors.length&&a.vectors.length===a.colors.length&&b.vectors.length===b.colors.length);
 assert([...a.vectors,...b.vectors].every(v=>v.length===3&&v.every(Number.isFinite)));
 if(a.vectors.length!==b.vectors.length)return null;
 const options=a.vectors.map((v,i)=>b.vectors.flatMap((w,j)=>color(a.colors[i])===color(b.colors[j])&&distance(v,w)<=radius+1e-10?[j]:[]));
 const owner=new Map();
 function augment(i,seen){for(const j of options[i]){if(seen.has(j))continue;seen.add(j);if(!owner.has(j)||augment(owner.get(j),seen)){owner.set(j,i);return true;}}return false;}
 for(const i of options.map((_,i)=>i).sort((i,j)=>options[i].length-options[j].length))if(!augment(i,new Set()))return null;
 const permutation=Array(a.vectors.length);for(const [j,i] of owner)permutation[i]=j;
 return {permutation,maxResidual:Math.max(...permutation.map((j,i)=>distance(a.vectors[i],b.vectors[j])))};
}
export function cloudConsensus(assignments,radius){
 assert(assignments.length);const ref=assignments[0],aligned=[];
 for(const a of assignments){const fit=cloudContains(a,ref,2*radius);if(!fit)return {status:'unknown'};const vectors=[];fit.permutation.forEach((j,i)=>vectors[j]=a.vectors[i]);aligned.push(vectors);}
 const mean=ref.vectors.map((_,i)=>[0,1,2].map(k=>aligned.reduce((sum,a)=>sum+a[i][k],0)/aligned.length));
 for(const vectors of [mean,...aligned]){
  const witness={vectors,colors:ref.colors},fits=assignments.map(a=>cloudContains(a,witness,radius));
  if(fits.every(Boolean))return {status:'verified-witness',witness,maxResidual:Math.max(...fits.map(f=>f.maxResidual))};
 }
 return {status:'unknown'}; // Not a complete intersection solver; never prune this.
}
const key=x=>JSON.stringify([x.point,x.channel??'portable']);
export function portableState(model,selected){
 const owners=new Map(),marks=new Map();let duplicate=false;
 for(const c of model.candidates)if(selected.has(c.id)){
  const base=c.base??c.id;if(owners.has(base))duplicate=true;owners.set(base,c.id);
  for(const m of c.cloudM||[]){const k=key(m);if(!marks.has(k))marks.set(k,[]);marks.get(k).push(m.cloud);}
 }
 return {owners,marks,duplicate};
}
export function portableWitnessCheck(model,selected){
 const state=portableState(model,selected);if(state.duplicate)return {valid:false,status:'inventory-conflict'};
 const witnesses=[];for(const [point,clouds] of state.marks){const result=cloudConsensus(clouds,model.cloudRadius);if(result.status!=='verified-witness')return {valid:false,status:'unknown-common-value',point};witnesses.push({point,...result});}
 return {valid:true,status:'verified-common-values',witnesses};
}
export function portableCloudClass(Base,model,{enabled=true}={}){
 assert(!model.expand&&model.complete!==false);assert(Number.isFinite(model.cloudRadius)&&model.cloudRadius>=0);
 const cloudIds=new Map();for(const c of model.candidates)for(const m of c.cloudM||[]){if(!cloudIds.has(m.cloud))cloudIds.set(m.cloud,cloudIds.size);}
 const pairCache=new Map();
 function compatible(a,b){
  if(a===b)return true;const ids=[cloudIds.get(a),cloudIds.get(b)].sort((x,y)=>x-y),k=ids.join(':');assert(ids.every(Number.isInteger));
  // Two memberships can each use the 1e-10 numerical guard. contains adds
  // one guard itself, so add the other here before applying triangle rejection.
  if(!pairCache.has(k))pairCache.set(k,cloudContains(a,b,2*model.cloudRadius+1e-10)!==null);
  return pairCache.get(k);
 }
 return class PortableSearch extends Base{
  addCandidate(c){
   super.addCandidate(c);
   for(const m of c.cloudM||[]){this.ensure(m.point);if(!this.dependencies.has(m.point))this.dependencies.set(m.point,new Set());this.dependencies.get(m.point).add(c.id);}
  }
  reason(c){
   const baseReason=super.reason(c);if(baseReason)return baseReason;
   if(this.portable?.owners.has(c.base??c.id))return 'shared-placement-inventory';
   if(enabled)for(const m of c.cloudM||[])for(const assigned of this.portable?.marks.get(key(m))||[])if(!compatible(m.cloud,assigned))return 'disjoint-portable-marking-sets';
   return null;
  }
  refresh(_changed){
   // Explicit complete rebuild includes extended mark-only dependencies and
   // variant inventory. Cache entries depend only on immutable cloud values.
   this.portable=portableState(model,new Set(this.placed.keys()));assert(!this.portable.duplicate);
   this.portableCompletion=undefined;super.refresh(new Set(this.points.keys()));
  }
  decision(){
   const d=super.decision();if(d.kind!=='complete'||!enabled)return d;
   this.portableCompletion=portableWitnessCheck(model,new Set(this.placed.keys()));
   return this.portableCompletion.valid?d:{kind:'unknown',reason:'Common portable marking value not yet certified'};
  }
 };
}
