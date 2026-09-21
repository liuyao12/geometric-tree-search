// Exact unmarked local-completion oracle. Geometry is display data only.
export const pointKey=p=>p.join(',');
export const add=(a,b)=>a.map((v,i)=>v+b[i]);
export const sub=(a,b)=>a.map((v,i)=>v-b[i]);
export const placementKey=p=>`${p.oi}@${p.translation}`;
export function allowedTranslation(model,p){
 const d=model.placementDomain;
 return p.every(Number.isSafeInteger)&&(!d||d.kind!=='a2_slab'||p.reduce((a,b)=>a+b,0)===0&&(!d.index3||(p[0]-p[1])%3===0&&(p[1]-p[2])%3===0));
}
export function validatePointModel(model){
 if(!Number.isSafeInteger(model.capacity)||model.capacity<1||!model.orientations?.length)throw Error('Learning needs an exact integer point model');
 for(const o of model.orientations)if(!o.cells?.length||new Set(o.cells.map(c=>pointKey(c.pos))).size!==o.cells.length||o.cells.some(c=>c.pos.length!==3||!c.pos.every(Number.isSafeInteger)||!Number.isSafeInteger(c.weight)||c.weight<1||c.weight>model.capacity))throw Error('Learning needs exact positive integer point weights');
}
export class CoronaGraph{
 constructor(model,{candidateLimit=100000,dependencyLimit=1000000}={}){validatePointModel(model);this.model=model;this.limit=candidateLimit;this.dependencyLimit=dependencyLimit;this.dependencyEntries=0;this.points=new Map();this.candidates=new Map();this.dependencies=new Map();this.totals=new Map();this.generations=new Map();this.selected=[];this.used=new Set();this.active=new Set();}
 legal(c){return !this.used.has(c.id)&&c.cells.every(p=>(this.totals.get(p.k)??0)+p.weight<=this.model.capacity);}
 candidate(oi,translation){
  const id=placementKey({oi,translation});if(this.candidates.has(id))return this.candidates.get(id);
  if(this.candidates.size>=this.limit){const e=Error('candidate budget');e.kind='resource_limit';throw e;}
  // Candidate count alone does not bound memory for large supports: a single
  // FCC candidate carries hundreds of entries in the reverse dependency graph.
  const entries=this.model.orientations[oi].cells.length;
  if(this.dependencyEntries+entries>this.dependencyLimit){const e=Error('candidate dependency budget');e.kind='resource_limit';throw e;}
  this.dependencyEntries+=entries;
  const c={id,oi,translation,cells:this.model.orientations[oi].cells.map(p=>({k:pointKey(add(p.pos,translation)),weight:p.weight})),points:new Set()};c.valid=this.legal(c);this.candidates.set(id,c);
  for(const p of c.cells){if(!this.dependencies.has(p.k))this.dependencies.set(p.k,new Set());this.dependencies.get(p.k).add(c);}return c;
 }
 point(k){
  if(this.points.has(k))return this.points.get(k);
  const pos=k.split(',').map(Number),p={k,pos,incident:new Set(),degree:0};this.points.set(k,p);
  for(let oi=0;oi<this.model.orientations.length;oi++)for(const a of this.model.orientations[oi].cells){const t=sub(pos,a.pos);if(!allowedTranslation(this.model,t))continue;const c=this.candidate(oi,t);if(p.incident.has(c))continue;p.incident.add(c);c.points.add(p);if(c.valid)p.degree++;}
  return p;
 }
 refresh(keys){
  const affected=new Set();
  for(const k of keys){for(const c of this.dependencies.get(k)??[])affected.add(c);const n=this.totals.get(k)??0;if(n>0&&n<this.model.capacity){this.point(k);this.active.add(k);}else this.active.delete(k);}
  for(const c of affected){const valid=this.legal(c);if(valid!==c.valid){for(const p of c.points)p.degree+=valid?1:-1;c.valid=valid;}}
 }
 apply(spec,{root=false}={}){
  if(!allowedTranslation(this.model,spec.translation))throw Error('Placement leaves learning lattice');
  const c=this.candidate(spec.oi,spec.translation);if(!this.legal(c))throw Error('Illegal oracle placement');
  const generation=root?0:1+Math.min(...c.cells.flatMap(p=>[...(this.generations.get(p.k)?.keys()??[])]));
  const undo=c.cells.map(p=>[p.k,this.totals.get(p.k),this.generations.get(p.k)]);
  this.selected.push(c);this.used.add(c.id);
  for(const p of c.cells){this.totals.set(p.k,(this.totals.get(p.k)??0)+p.weight);const counts=new Map(this.generations.get(p.k));counts.set(generation,(counts.get(generation)??0)+1);this.generations.set(p.k,counts);}
  this.refresh(c.cells.map(p=>p.k));return undo;
 }
 rollback(undo){const c=this.selected.pop();this.used.delete(c.id);for(const [k,n,g] of undo){if(n===undefined){this.totals.delete(k);this.generations.delete(k);}else{this.totals.set(k,n);this.generations.set(k,g);}}this.refresh(undo.map(([k])=>k));}
 schedule(){let forced=null,branch=null;
  for(const k of this.active){const p=this.points.get(k);if(!p.degree)return {kind:'dead',point:p};if(p.degree===1)forced??=p;const generation=Math.min(...this.generations.get(k).keys());if(!branch||generation<branch.generation||generation===branch.generation&&p.degree<branch.point.degree)branch={point:p,generation};}
  return {kind:forced?'forced':branch?'branch':'closed',point:forced??branch?.point};
 }
 descriptors(){return this.selected.map(c=>({oi:c.oi,translation:[...c.translation]}));}
 audit(){for(const p of this.points.values()){const valid=[...p.incident].filter(c=>this.legal(c));if(valid.length!==p.degree||[...p.incident].some(c=>c.valid!==this.legal(c)))throw Error('Oracle incidence mismatch');}return true;}
}
// Independent replay, including complete candidate enumeration at every exposed
// point. A finite pair core can be filled while its outer frontier is dead.
export function verifyCorona(model,pair,placements){
 const totals=new Map(),used=new Set(),core=new Set();
 for(const p of pair)for(const c of model.orientations[p.oi].cells)core.add(pointKey(add(c.pos,p.translation)));
 for(const p of placements){const o=model.orientations[p.oi],id=placementKey(p);if(!o||used.has(id)||!allowedTranslation(model,p.translation))throw Error('Invalid corona placement');used.add(id);for(const c of o.cells){const k=pointKey(add(c.pos,p.translation)),n=(totals.get(k)??0)+c.weight;if(n>model.capacity)throw Error('Corona capacity exceeded');totals.set(k,n);}}
 if(pair.some(p=>!used.has(placementKey(p))))throw Error('Corona lost its seed pair');
 const dead=[];
 for(const [k,n] of totals){if(n===model.capacity)continue;const pos=k.split(',').map(Number);let viable=false;
  outer:for(let oi=0;oi<model.orientations.length;oi++)for(const a of model.orientations[oi].cells){const t=sub(pos,a.pos);if(!allowedTranslation(model,t)||used.has(placementKey({oi,translation:t})))continue;if(model.orientations[oi].cells.every(c=>(totals.get(pointKey(add(c.pos,t)))??0)+c.weight<=model.capacity)){viable=true;break outer;}}
  if(!viable)dead.push(pos);
 }
 return {complete:[...core].every(k=>totals.get(k)===model.capacity)&&!dead.length,coreComplete:[...core].every(k=>totals.get(k)===model.capacity),frontierViable:!dead.length,deadPoints:dead};
}
export async function* checkCorona(model,pair,{nodes=500,deadline=Infinity,stop=()=>false,audit=false,candidateLimit=100000,dependencyLimit=1000000}={}){
 let graph,n=0,backtracks=0,reason=null,last=0,best=pair,won=false;const core=new Set(pair.flatMap(p=>model.orientations[p.oi].cells.map(c=>pointKey(add(c.pos,p.translation)))));
 const expired=()=>{if(stop())reason='cancelled';else if(performance.now()>=deadline)reason='time budget';else if(n>=nodes)reason='attempt budget';return !!reason;};
 async function* visit(depth){
  if(expired())return false;if(depth>256){reason='depth budget';return false;}
  const s=graph.schedule();if(audit)graph.audit();
  if(s.kind==='dead'){yield {type:'corona-step',action:'dead',point:s.point.pos,placements:graph.descriptors(),nodes:n,backtracks};return false;}
  if([...core].every(k=>graph.totals.get(k)===model.capacity))return true;
  if(!s.point)throw Error('Incomplete core without an obligation');
  // Branch order is generation first, degree only breaking generation ties.
  for(const c of s.point.incident){if(!c.valid)continue;if(expired())return false;n++;const undo=graph.apply(c);best=graph.descriptors();
   if(performance.now()-last>35){last=performance.now();yield {type:'corona-step',action:s.kind==='forced'?'forced':'place',placements:best,nodes:n,backtracks};await new Promise(r=>setTimeout(r,0));}
   if(yield* visit(depth+1))return true;
   graph.rollback(undo);backtracks++;if(audit)graph.audit();if(reason)return false;
  }return false;
 }
 try{graph=new CoronaGraph(model,{candidateLimit,dependencyLimit});for(const p of pair)graph.apply(p,{root:true});won=yield* visit(0);if(won){best=graph.descriptors();if(!verifyCorona(model,pair,best).complete)throw Error('Independent corona verification failed');}}
 catch(e){if(e.kind!=='resource_limit')throw e;reason=e.message;}
 yield {type:'corona-result',status:won?'valid':reason?'unresolved':'invalid',reason,placements:best,nodes:n,backtracks,verification:won?verifyCorona(model,pair,best):null};
}
