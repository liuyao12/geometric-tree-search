import {selectMask} from './marking-mask.js?v=20260921-free-components';
import {pointKey,add,sub,placementKey,allowedTranslation,validatePointModel,checkCorona} from './corona-graph.js?v=20260921-free-components';
export const LEARNING_VERSION='pair-corona-marking-2';
const permutations=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
const minimum=cells=>[0,1,2].map(i=>Math.min(...cells.map(c=>c.pos[i])));
const signature=cells=>cells.map(c=>`${c.pos}:${c.weight}`).sort().join('|');
// Point-group operations must preserve each species' declared orientation set.
// The resulting code labels carry the induced permutation representation.
export function pointSymmetries(model){
 const lookup=new Map();model.orientations.forEach((o,oi)=>{const origin=minimum(o.cells);lookup.set(`${o.type}|${signature(o.cells.map(c=>({...c,pos:sub(c.pos,origin)})))}`,{oi,origin});});
 const transforms=[];
 for(const permutation of permutations)for(let mask=0;mask<8;mask++){
  const signs=[0,1,2].map(i=>mask&(1<<i)?-1:1);if(!model.allowReflections&&parity(permutation)*signs.reduce((a,b)=>a*b,1)<0)continue;
  const transform=p=>permutation.map((j,i)=>p[j]*signs[i]),map=[];
  for(const o of model.orientations){const cells=o.cells.map(c=>({...c,pos:transform(c.pos)})),origin=minimum(cells),match=lookup.get(`${o.type}|${signature(cells.map(c=>({...c,pos:sub(c.pos,origin)})))}`);if(!match)break;map.push({oi:match.oi,shift:sub(origin,match.origin)});}
  if(map.length!==model.orientations.length)continue;
  if(model.placementDomain?.kind==='a2_slab'&&[[1,1,-2],[-1,2,-1]].some(p=>!allowedTranslation(model,transform(p))))continue;
  transforms.push({permutation,signs,transform,map});
 }
 if(!transforms.length)throw Error('No point-group identity for this model');return transforms;
}
export function* neighboringPairs(model,transforms,{maxPairs=20000}={}){
 const covered=new Set();let count=0;
 for(let root=0;root<model.orientations.length;root++){
  if(covered.has(root))continue;covered.add(root);for(const g of transforms)covered.add(g.map[root].oi);
  const weights=new Map(model.orientations[root].cells.map(c=>[pointKey(c.pos),c.weight])),seen=new Set();
  for(let oi=0;oi<model.orientations.length;oi++)for(const anchor of model.orientations[oi].cells)for(const at of model.orientations[root].cells){
   const translation=sub(at.pos,anchor.pos),id=placementKey({oi,translation});if(seen.has(id)||oi===root&&translation.every(x=>x===0)||!allowedTranslation(model,translation))continue;seen.add(id);
   if(model.orientations[oi].cells.some(c=>(weights.get(pointKey(add(c.pos,translation)))??0)+c.weight>model.capacity))continue;
   if(count++>=maxPairs){const e=Error('pair catalog budget');e.kind='resource_limit';throw e;}
   yield [{oi:root,translation:[0,0,0]},{oi,translation}];
  }
 }
}
export function markingDomain(model,extent=1){
 let steps=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
 if(model.placementDomain?.kind==='a2_slab'){const a=model.placementDomain.index3?[1,1,-2]:[1,0,-1],b=model.placementDomain.index3?[-1,2,-1]:[0,1,-1];steps=[a,b,sub(a,b)].flatMap(p=>[p,p.map(v=>-v)]);}
 return model.orientations.map((o,oi)=>{const points=new Map(o.cells.map(c=>[pointKey(c.pos),c.pos]));for(let n=0;n<extent;n++)for(const p of [...points.values()])for(const d of steps){const q=add(p,d);points.set(pointKey(q),q);}return [...points.values()].map(pos=>({oi,pos:[...pos],component:0}));});
}
export class OnlineMarking{
 constructor(model,transforms,{extent=1,maxSlots=12000,maskLearning=true}={}){
  this.maskLearning=maskLearning;this.positiveEdges=new Map();this.previousMask=null;this.model=model;this.transforms=transforms;this.extent=extent;this.byOrientation=markingDomain(model,extent);this.slots=this.byOrientation.flat();if(this.slots.length>maxSlots){const e=Error('marking support budget');e.kind='resource_limit';throw e;}
  this.slots.forEach((s,i)=>s.id=i);this.parent=this.slots.map((_,i)=>i);this.rows=[];this.counts={valid:0,invalid:0,unresolved:0};
  const lookup=new Map(this.slots.map(s=>[`${s.oi}:${s.pos}`,s.id]));
  this.actions=transforms.map(g=>this.slots.map(s=>{const target=g.map[s.oi],index=lookup.get(`${target.oi}:${sub(g.transform(s.pos),target.shift)}`);if(index===undefined)throw Error('Marking support is not closed under the point group');return index;}));
  this.orbits=[];const seen=new Set();for(const s of this.slots)if(!seen.has(s.id)){const orbit=[...new Set([s.id,...this.actions.map(a=>a[s.id])])];orbit.forEach(i=>seen.add(i));this.orbits.push(orbit);}
 }
 find(i){while(this.parent[i]!==i){this.parent[i]=this.parent[this.parent[i]];i=this.parent[i];}return i;}
 join(i,j){i=this.find(i);j=this.find(j);if(i!==j)this.parent[Math.max(i,j)]=Math.min(i,j);}
 contacts(pair){const seen=new Map(),contacts=[];for(const p of pair)for(const s of this.byOrientation[p.oi]){const k=pointKey(add(s.pos,p.translation));if(seen.has(k))contacts.push([seen.get(k),s.id]);else seen.set(k,s.id);}return contacts;}
 add(row){
  const started=performance.now();if(!Object.hasOwn(this.counts,row.status))throw Error('Unknown label');const contacts=this.contacts(row.pair);this.rows.push({...row,contacts});this.counts[row.status]++;
  if(row.status==='valid')for(const [i,j] of contacts)for(const action of this.actions){const a=action[i],b=action[j];this.join(a,b);if(this.maskLearning&&a!==b)this.positiveEdges.set(Math.min(a,b)*this.slots.length+Math.max(a,b),[a,b]);}
  return this.snapshot({started});
 }
 snapshot({started=performance.now(),maxEvaluations=64}={}){
  const labels=new Map(),values=this.slots.map((_,i)=>{const r=this.find(i);if(!labels.has(r))labels.set(r,labels.size+1);return labels.get(r);});
  // Keep a witness for every negative currently distinguished. Free variables
  // are omitted, not replaced by zero. Delete complete symmetry orbits so the
  // wildcard mask transforms with the tile, without privileging the interior.
  const witnesses=this.rows.filter(r=>r.status==='invalid').map(r=>r.contacts.filter(([i,j])=>values[i]!==values[j])).filter(w=>w.length),kept=new Set(this.slots.map(s=>s.id));
  if(this.counts.valid)for(const orbit of this.orbits){orbit.forEach(i=>kept.delete(i));if(witnesses.some(w=>!w.some(([i,j])=>kept.has(i)&&kept.has(j))))orbit.forEach(i=>kept.add(i));}
  // Before the first positive, all values are provisional independent labels.
  const fields=this.byOrientation.map(list=>list.filter(s=>kept.has(s.id)).map(s=>({pos:s.pos,component:0,value:values[s.id]})));
  const positivePassed=this.rows.filter(r=>r.status==='valid'&&r.contacts.every(([i,j])=>!kept.has(i)||!kept.has(j)||values[i]===values[j])).length;
  const negativeBlocked=this.rows.filter(r=>r.status==='invalid'&&r.contacts.some(([i,j])=>kept.has(i)&&kept.has(j)&&values[i]!==values[j])).length;
  const representation=this.actions.map(action=>{const mapping={};for(let i=0;i<values.length;i++){if(mapping[values[i]]!==undefined&&mapping[values[i]]!==values[action[i]])throw Error('Non-equivariant learned labels');mapping[values[i]]=values[action[i]];}if(new Set(Object.values(mapping)).size!==labels.size)throw Error('Noninvertible label action');return mapping;});
  const baseline={version:LEARNING_VERSION,fields,counts:{...this.counts},pairs:this.rows.length,positivePassed,negativeBlocked,points:fields.reduce((n,f)=>n+f.length,0),values:fields.reduce((n,f)=>n+f.length,0),labelCount:labels.size,representation,extent:this.extent,updateMs:performance.now()-started,scope:'Provisional scalar point codes with a point-group permutation of labels; finite pair evidence only.'};
  if(!this.maskLearning||!this.counts.valid||!this.counts.invalid)return baseline;
  const chosen=selectMask(this.slots.length,this.orbits,[...this.positiveEdges.values()],this.rows.filter(r=>r.status==='invalid').map(r=>r.contacts),{
   initialMasks:[this.orbits.map(o=>kept.has(o[0])),this.previousMask],maxEvaluations,seed:this.rows.length,
  });
  this.previousMask=chosen.mask;
  // Keep the legacy separator when it is stronger or equally sparse. Every
  // proposed mask is scored against the entire currently labeled prefix.
  if(chosen.blocked<baseline.negativeBlocked||chosen.blocked===baseline.negativeBlocked&&chosen.points>=baseline.points)return {...baseline,updateMs:performance.now()-started};
  const codes=new Map(),assigned=this.slots.map((_,i)=>{if(!chosen.active[i])return null;const r=chosen.find(i);if(!codes.has(r))codes.set(r,codes.size+1);return codes.get(r);});
  const maskedFields=this.byOrientation.map(list=>list.filter(s=>chosen.active[s.id]).map(s=>({pos:s.pos,component:s.component,value:assigned[s.id]})));
  const maskedRepresentation=this.actions.map(action=>{const mapping={};for(let i=0;i<assigned.length;i++)if(chosen.active[i]){const a=assigned[i],b=assigned[action[i]];if(b===null||mapping[a]!==undefined&&mapping[a]!==b)throw Error('Non-equivariant free-value marking');mapping[a]=b;}if(new Set(Object.values(mapping)).size!==codes.size)throw Error('Noninvertible free-value action');return mapping;});
  const passed=this.rows.filter(r=>r.status==='valid'&&pairCompatible(maskedFields,r.pair)).length;
  const blocked=this.rows.filter(r=>r.status==='invalid'&&!pairCompatible(maskedFields,r.pair)).length;
  if(passed!==this.counts.valid||blocked!==chosen.blocked)throw Error('Free-value marking replay failed');
  return {...baseline,fields:maskedFields,representation:maskedRepresentation,labelCount:codes.size,positivePassed:passed,negativeBlocked:blocked,points:chosen.points,values:chosen.points,updateMs:performance.now()-started,scope:'Conditional positive equalities with symmetry-preserving free-value support search; finite pair evidence only.'};
 }
}
export function pairCompatible(fields,pair){const section=new Map();for(const p of pair)for(const m of fields[p.oi]){const k=`${add(m.pos,p.translation)}|${m.component??0}`;if(section.has(k)&&section.get(k)!==m.value)return false;section.set(k,m.value);}return true;}
export async function* learnMarking(model,{timeMs=10000,pairNodes=500,maxPairs=20000,maxSlots=12000,extent=1,stop=()=>false,audit=false}={}){
 const started=performance.now(),deadline=started+timeMs;let snapshot=null,reason=null,complete=false,trainer,transforms;const evidence=[];
 try{
  validatePointModel(model);transforms=pointSymmetries(model);trainer=new OnlineMarking(model,transforms,{extent,maxSlots});
  for(const pair of neighboringPairs(model,transforms,{maxPairs})){
   if(stop()||performance.now()>=deadline){reason=stop()?'cancelled':'learning time budget';break;}
   yield {type:'marking-learning',phase:'pair',pair,placements:pair,pairs:evidence.length,counts:{...trainer.counts},snapshot,elapsedMs:performance.now()-started};let row;
   for await(const e of checkCorona(model,pair,{nodes:pairNodes,deadline,stop,audit})){
    if(e.type==='corona-step')yield {...e,type:'marking-learning',phase:'corona',pair,pairs:evidence.length,counts:{...trainer.counts},snapshot,elapsedMs:performance.now()-started};else row=e;
   }
   row={...row,pair};evidence.push(row);snapshot=trainer.add(row);
   yield {type:'marking-learning',phase:'update',pair,placements:row.placements,snapshot,pairs:evidence.length,counts:snapshot.counts,status:row.status,elapsedMs:performance.now()-started};await new Promise(r=>setTimeout(r,0));
  }
  complete=!reason;
 }catch(e){if(e.kind!=='resource_limit')throw e;reason=e.message;}
 if(snapshot&&complete&&trainer.maskLearning){
  snapshot=trainer.snapshot({maxEvaluations:2048});
  yield {type:'marking-learning',phase:'refine',snapshot,pairs:evidence.length,counts:snapshot.counts,elapsedMs:performance.now()-started};
 }
 if(snapshot){
  let positivePassed=0,negativeBlocked=0;
  for(const row of evidence){const compatible=pairCompatible(snapshot.fields,row.pair);if(row.status==='valid'&&compatible)positivePassed++;if(row.status==='invalid'&&!compatible)negativeBlocked++;}
  if(positivePassed!==snapshot.counts.valid)throw Error('Marking rejects a positive pair');
  if(positivePassed!==snapshot.positivePassed||negativeBlocked!==snapshot.negativeBlocked)throw Error('Independent marking replay disagrees with training scores');
 }
 const qualifies=!!snapshot&&complete&&!snapshot.counts.unresolved&&snapshot.counts.valid>0&&snapshot.positivePassed===snapshot.counts.valid&&(snapshot.counts.invalid===0||snapshot.negativeBlocked*2>snapshot.counts.invalid);
 const result={...snapshot,version:LEARNING_VERSION,complete,accepted:qualifies,reason:reason??(snapshot?.counts.unresolved?'unresolved pairs':!qualifies?'marking did not pass acceptance':null),evidence,elapsedMs:performance.now()-started,scope:'Learned restriction supported by viable pair-corona labels; neither redundant pruning nor an infinite-tiling certificate.'};
 yield {type:'marking-learned',marking:result,model:qualifies?{...model,orientations:model.orientations.map((o,i)=>({...o,marks:snapshot.fields[i]}))}:null};
}
// Adapter used by the legacy engine; ordinary exact section matching, no scan
// of a runtime forbidden-pair classifier. The marking is frozen before growth.
export class LearnedSection{
 constructor(model,marking){this.model=model;this.marking=marking;this.section=new Map();this.conflicts=0;this.lookup=new Map(model.orientations.map((o,i)=>[`${o.type}:${o.index}`,i]));}
 entries(move){const oi=this.lookup.get(`${move.type}:${move.index}`);return this.marking.fields[oi].map(m=>({key:`${add(m.pos,move.translation)}|${m.component??0}`,basis:m.value}));}
 compatible(move){return !this.conflicts&&this.entries(move).every(s=>!this.section.has(s.key)||this.section.get(s.key).value===s.basis);}
 add(move){for(const s of this.entries(move)){const old=this.section.get(s.key);if(old&&old.value!==s.basis)throw Error('Incompatible marking prefix');this.section.set(s.key,{value:s.basis,count:(old?.count??0)+1});}}
 remove(move){for(const s of this.entries(move)){const old=this.section.get(s.key);if(--old.count===0)this.section.delete(s.key);}}
 observeDeadPoint(){return false;}
 stats(){return {marking_rank:this.marking.labelCount,marking_slots:this.marking.values,marking_revision:this.marking.pairs,marking_certified_pairs:0,marking_learned_pairs:this.marking.pairs,marking_valid_passed:this.marking.positivePassed,marking_invalid_blocked:this.marking.negativeBlocked,marking_learning_ms:this.marking.elapsedMs,marking_scope:this.marking.scope,global_section_points:this.section.size,global_section_conflicts:0,marking_memory_bytes:this.marking.values*40+this.section.size*48};}
}
