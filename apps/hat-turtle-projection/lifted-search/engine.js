import {CAPACITY,ORIENTATIONS,materialize,sub,MODEL_INFO,compactPlacement,dependencyChunk} from './model.js';
const same=(a,b)=>a.length===b.length&&a.every((x,k)=>x===b[k]);
const cloneRow=r=>r?{...r,legal:new Set(r.legal)}:null;
const clonePoint=p=>p?{...p,lift:p.lift?[...p.lift]:null}:null;
export class LiftedSearch {
 constructor({target=20,nodeLimit=10000,seed=1,audit=false}={}){
  this.target=target;this.nodeLimit=nodeLimit;this.rng=seed>>>0||1;this.audit=audit;
  this.points=new Map();this.rows=new Map();this.pool=new Map();this.dependents=new Map();this.incidence=new Map();this.validity=new Map();this.used=new Set();this.placed=[];
  this.stats={attempts:0,forced:0,branches:0,backtracks:0,capacityHat:0,capacityTurtle:0,markingHat:0,markingTurtle:0,graphAudits:0};
  this.status='ready';this.best=[];this.bestViable=[];this.lastChoice=null;this.stopped=false;
  this.apply(this.candidate(0,[0,0,0,0]),0);this.status='ready';this.iterator=this.search();
 }
 random(){this.rng=(Math.imul(this.rng,1664525)+1013904223)>>>0;return this.rng/4294967296;}
 candidate(o,t){const id=`${o}|${t.join(',')}`;if(this.pool.has(id))return this.pool.get(id);
  const c=compactPlacement(o,t);this.pool.set(id,c);
  for(const k of c.chunks){if(!this.dependents.has(k))this.dependents.set(k,new Set());this.dependents.get(k).add(id);}
  return c;
 }
 reason(c){if(this.used.has(c.id))return 'used';
  for(const e of c.support){const p=this.points.get(e.key);if((p?.total||0)+e.weight>CAPACITY)return e.layer==='h'?'capacityHat':'capacityTurtle';
   if(e.lift&&p?.lift&&!same(e.lift,p.lift))return e.layer==='h'?'markingHat':'markingTurtle';}
  return null;
 }
 candidatesAt(p){
  if(!p.lift||p.total<=0||p.total>=12)throw Error('Growth frontier must have a lifted boundary vertex');
  const out=new Map();
  // Capacity 12 interior samples cannot fit any positive frontier deficit.
  // All remaining positive alignments are the fourteen boundary vertices.
  for(const o of ORIENTATIONS)for(const e of o.anchors){
   if(e.layer!==p.layer||!e.lift||e.weight>12-p.total)continue;
   const c=this.candidate(o.index,sub(p.lift,e.lift));out.set(c.id,c);
  }
  return [...out.values()];
 }
 rebuildRow(k,delta){
  const p=this.points.get(k);this.rememberRow(delta,k);
  if(!p||p.total===12){this.rows.delete(k);return;}
  const candidates=this.candidatesAt(p),legal=new Set();
  for(const c of candidates){
   if(!this.incidence.has(c.id))this.incidence.set(c.id,new Set());this.incidence.get(c.id).add(k);
   this.rememberValidity(delta,c.id);const why=this.reason(c);this.validity.set(c.id,!why);if(!why)legal.add(c.id);
  }
  this.rows.set(k,{key:k,generation:p.generation,candidates,legal});
 }
 rememberRow(d,k){if(d&&!d.rows.has(k))d.rows.set(k,cloneRow(this.rows.get(k)));}
 rememberValidity(d,k){if(d&&!d.validity.has(k))d.validity.set(k,this.validity.has(k)?this.validity.get(k):undefined);}
 apply(c,generation){
  const d={points:new Map(),rows:new Map(),validity:new Map(),id:c.id};
  for(const e of c.support){d.points.set(e.key,clonePoint(this.points.get(e.key)));const old=this.points.get(e.key);
   const p=old?{...old}:{key:e.key,layer:e.layer,x:e.x,y:e.y,total:0,lift:null,markCount:0,generation};
   p.total+=e.weight;if(p.total>12)throw Error('Illegal capacity mutation');p.generation=Math.min(p.generation,generation);
   if(e.lift){if(p.lift&&!same(p.lift,e.lift))throw Error('Illegal lift mutation');p.lift=e.lift;p.markCount++;}
   this.points.set(e.key,p);
  }
  this.placed.push(Object.assign(Object.create(c),{generation}));this.used.add(c.id);
  const affected=new Set();for(const k of d.points.keys())for(const id of this.dependents.get(dependencyChunk(this.points.get(k)))||[])affected.add(id);
  for(const id of affected){
   this.rememberValidity(d,id);const why=this.reason(this.pool.get(id)),was=this.validity.get(id);this.validity.set(id,!why);
   if(was&&!this.validity.get(id)&&why!=='used')this.stats[why]++;
   for(const k of this.incidence.get(id)||[]){const row=this.rows.get(k);if(!row||!row.candidates.some(c=>c.id===id))continue;this.rememberRow(d,k);
    if(why)row.legal.delete(id);else row.legal.add(id);
   }
  }
  for(const k of d.points.keys()){
   const p=this.points.get(k),row=this.rows.get(k);
   if(p.total===12){if(row){this.rememberRow(d,k);this.rows.delete(k);}}
   else if(!row)this.rebuildRow(k,d);
   else{this.rememberRow(d,k);row.generation=p.generation;}
  }
  if(this.placed.length>this.best.length)this.best=this.placed.map(c=>({orientation:c.orientation,translation:[...c.translation],generation:c.generation}));return d;
 }
 undo(d){
  if(this.placed.at(-1)?.id!==d.id)throw Error('Rollback order mismatch');this.placed.pop();this.used.delete(d.id);
  for(const [k,p] of d.points){if(p)this.points.set(k,p);else this.points.delete(k);}
  for(const [k,row] of d.rows){if(row)this.rows.set(k,row);else this.rows.delete(k);}
  for(const [k,v] of d.validity){if(v===undefined)this.validity.delete(k);else this.validity.set(k,v);}
 }
 auditGraph(){
  const active=[...this.points.values()].filter(p=>p.total<12);
  if(active.length!==this.rows.size)throw Error('Frontier size mismatch');
  for(const p of active){const row=this.rows.get(p.key);if(!row||row.generation!==p.generation)throw Error('Missing frontier row');
   const brute=new Set(this.candidatesAt(p).filter(c=>!this.reason(c)).map(c=>c.id));
   if(brute.size!==row.legal.size||[...brute].some(id=>!row.legal.has(id)))throw Error(`Incomplete candidate domain at ${p.key}`);
  }
  this.stats.graphAudits++;
 }
 choice(){
  if(this.audit)this.auditGraph();const rows=[...this.rows.values()];
  const dead=rows.find(r=>r.legal.size===0);if(dead)return {kind:'dead',row:dead};
  const compare=(a,b)=>a.generation-b.generation||a.legal.size-b.legal.size||a.key.localeCompare(b.key);
  const forced=rows.filter(r=>r.legal.size===1).sort(compare);if(forced.length)return {kind:'forced',row:forced[0]};
  rows.sort(compare);return rows.length?{kind:'branch',row:rows[0]}:{kind:'complete',row:null};
 }
 *search(){
  if(this.stopped||this.stats.attempts>=this.nodeLimit||this.pool.size>30000)return 'unknown';
  const pick=this.choice();this.lastChoice={kind:pick.kind,key:pick.row?.key,generation:pick.row?.generation,degree:pick.row?.legal.size};
  yield {type:pick.kind};if(pick.kind==='dead')return false;
  if(this.placed.length>this.bestViable.length)this.bestViable=this.placed.map(c=>({orientation:c.orientation,translation:[...c.translation],generation:c.generation}));
  if(this.placed.length>=this.target||pick.kind==='complete')return 'checkpoint';
  const options=[...pick.row.legal].map(id=>({c:this.pool.get(id),tie:this.random()}));
  for(const item of options){let contacts=0,fills=0;for(const e of item.c.support){const p=this.points.get(e.key);if(p){contacts++;if(p.total+e.weight===12)fills++;}}item.score=fills*100+contacts;}
  options.sort((a,b)=>b.score-a.score||a.tie-b.tie);
  if(pick.kind==='branch')this.stats.branches++;
  for(const {c} of options){
   if(this.stopped||this.stats.attempts>=this.nodeLimit||this.pool.size>30000)return 'unknown';if(this.reason(c))continue;
   this.stats.attempts++;if(pick.kind==='forced')this.stats.forced++;
   const gen=1+Math.min(...[...c.support].flatMap(e=>this.points.has(e.key)?[this.points.get(e.key).generation]:[]));
   const d=this.apply(c,gen);yield {type:'placement',id:c.id};
   const result=yield* this.search();if(result==='checkpoint')return result;
   this.undo(d);this.stats.backtracks++;yield {type:'rollback'};
   if(result==='unknown')return result;
  }
  return false;
 }
 step(){const r=this.iterator.next();if(r.done){this.status=r.value==='checkpoint'?'consistent finite patch':r.value===false?'exhausted rooted search':'unknown';return {done:true,status:this.status};}this.status='searching';return {done:false,...r.value};}
 snapshot(placements=this.placed){return {version:MODEL_INFO.version,status:this.status,placements:placements.map(c=>({orientation:c.orientation,translation:c.translation,generation:c.generation})),stats:{...this.stats,candidates:this.pool.size,frontierPoints:this.rows.size,pointNodes:this.points.size},choice:this.lastChoice,target:this.target,nodeLimit:this.nodeLimit};}
 // The immutable candidate/dependency cache is deliberately excluded: it has no
 // branch state. All totals, marks, generations, domains and validity are trailed.
 fingerprint(){return JSON.stringify({points:[...this.points].sort().map(([k,p])=>[k,p.total,p.generation,p.lift,p.markCount]),rows:[...this.rows].sort().map(([k,r])=>[k,r.generation,[...r.legal].sort()]),used:[...this.used].sort(),validity:[...this.validity].sort()});}
}
export function verify(specs){
 const points=new Map(),seen=new Set(),edges=new Map(),vertices=new Set();
 for(const spec of specs){const c=materialize(spec.orientation,spec.translation);if(seen.has(c.id))throw Error('Duplicate placement');seen.add(c.id);
  for(const e of c.support){const p=points.get(e.key)||{total:0,lift:null};p.total+=e.weight;if(p.total>12)throw Error(`Capacity mismatch ${e.key}`);if(e.lift&&p.lift&&!same(e.lift,p.lift))throw Error('Inconsistent shared lift');if(e.lift)p.lift=e.lift;points.set(e.key,p);}
  for(let i=0;i<14;i++){const a=c.vertices[i].join(','),b=c.vertices[(i+1)%14].join(',');vertices.add(a);const k=a<b?`${a}|${b}`:`${b}|${a}`;edges.set(k,(edges.get(k)||0)+1);}
 }
 if([...edges.values()].some(n=>n>2))throw Error('Non-manifold edge incidence');
 const open=[...points].filter(([,p])=>p.total<12).length;
 return {tiles:specs.length,points:points.size,openVertexObligations:open,surfaceVertices:vertices.size,surfaceEdges:edges.size,eulerCharacteristic:vertices.size-edges.size+specs.length,sharedEdges:[...edges.values()].filter(n=>n===2).length,boundaryEdges:[...edges.values()].filter(n=>n===1).length,hatAndTurtleCapacities:true,sharedLiftMarkings:true,scope:'Consistent finite patch; open boundary, no infinite extension claim'};
}
