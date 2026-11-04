import {createPointModel,key,sub,VERSION} from './j-point-model.js';
const cloneRow=r=>r?{...r,legal:new Set(r.legal)}:null;
export class JPointSearch{
 constructor({target=100,nodeLimit=20000,seed=1,audit=false,branch='mixed',support='corners'}={}){
  this.model=createPointModel({branch,support});this.target=target;this.nodeLimit=nodeLimit;this.rng=seed>>>0||1;this.audit=audit;this.status='ready';this.stopped=false;
  this.points=new Map();this.rows=new Map();this.pool=new Map();this.dependents=new Map();this.incidence=new Map();this.validity=new Map();this.used=new Set();this.placed=[];this.bestViable=[];this.lastChoice=null;
  this.stats={attempts:0,forced:0,branches:0,backtracks:0,capacityRejections:0,graphAudits:0};
  this.apply(this.candidate(0,[0,0,0,0]),0);this.iterator=this.search();
 }
 random(){this.rng=(Math.imul(this.rng,1664525)+1013904223)>>>0;return this.rng/4294967296;}
 candidate(o,t){const id=`${o}|${key(t)}`;if(this.pool.has(id))return this.pool.get(id);
  const c=this.model.materialize(o,t);this.pool.set(id,c);
  for(const e of c.corners){if(!this.dependents.has(e.key))this.dependents.set(e.key,new Set());this.dependents.get(e.key).add(id);}return c;
 }
 reason(c){if(this.used.has(c.id))return'used';for(const e of c.corners)if((this.points.get(e.key)?.total??0)+e.weight>12)return'capacity';return null;}
 candidatesAt(p){const out=new Map();for(const o of this.model.ORIENTATIONS)for(const a of o.corners){if(a.weight>12-p.total)continue;const t=sub(p.point,a.point);if(!this.model.validTranslation(t))continue;const c=this.candidate(o.index,t);out.set(c.id,c);}return[...out.values()];}
 rememberRow(d,k){if(d&&!d.rows.has(k))d.rows.set(k,cloneRow(this.rows.get(k)));}
 rememberValidity(d,k){if(d&&!d.validity.has(k))d.validity.set(k,this.validity.has(k)?this.validity.get(k):undefined);}
 rebuildRow(k,d){const p=this.points.get(k);this.rememberRow(d,k);if(!p||p.total===12){this.rows.delete(k);return;}
  const candidates=this.candidatesAt(p),legal=new Set();for(const c of candidates){if(!this.incidence.has(c.id))this.incidence.set(c.id,new Set());this.incidence.get(c.id).add(k);this.rememberValidity(d,c.id);const ok=!this.reason(c);this.validity.set(c.id,ok);if(ok)legal.add(c.id);}
  this.rows.set(k,{key:k,generation:p.generation,candidates,legal});
 }
 apply(c,generation){if(this.reason(c))throw Error('Illegal placement');const d={id:c.id,points:new Map(),rows:new Map(),validity:new Map()};
  for(const e of c.corners){const old=this.points.get(e.key);d.points.set(e.key,old?{...old}:null);this.points.set(e.key,{point:e.point,total:(old?.total??0)+e.weight,generation:Math.min(old?.generation??generation,generation)});}
  this.used.add(c.id);this.placed.push({orientation:c.orientation,translation:c.translation,generation,id:c.id});
  const affected=new Set();for(const k of d.points.keys())for(const id of this.dependents.get(k)??[])affected.add(id);
  for(const id of affected){this.rememberValidity(d,id);const ok=!this.reason(this.pool.get(id)),was=this.validity.get(id);this.validity.set(id,ok);if(was&&!ok&&!this.used.has(id))this.stats.capacityRejections++;
   for(const k of this.incidence.get(id)??[]){const row=this.rows.get(k);if(!row||!row.candidates.some(x=>x.id===id))continue;this.rememberRow(d,k);if(ok)row.legal.add(id);else row.legal.delete(id);}
  }
  for(const k of d.points.keys()){const p=this.points.get(k),row=this.rows.get(k);if(p.total===12){if(row){this.rememberRow(d,k);this.rows.delete(k);}}else if(!row)this.rebuildRow(k,d);else{this.rememberRow(d,k);row.generation=p.generation;}}
  return d;
 }
 undo(d){if(this.placed.at(-1)?.id!==d.id)throw Error('Rollback order');this.placed.pop();this.used.delete(d.id);
  for(const[k,v]of d.points){if(v)this.points.set(k,v);else this.points.delete(k);}for(const[k,v]of d.rows){if(v)this.rows.set(k,v);else this.rows.delete(k);}for(const[k,v]of d.validity){if(v===undefined)this.validity.delete(k);else this.validity.set(k,v);}
 }
 auditGraph(){const active=[...this.points].filter(([,p])=>p.total<12);if(active.length!==this.rows.size)throw Error('Frontier count');
  for(const[k,p]of active){const row=this.rows.get(k),brute=new Set(this.candidatesAt(p).filter(c=>!this.reason(c)).map(c=>c.id));if(!row||row.generation!==p.generation||brute.size!==row.legal.size||[...brute].some(id=>!row.legal.has(id)))throw Error('Frontier divergence '+k);}
  this.stats.graphAudits++;
 }
 choice(){if(this.audit)this.auditGraph();const rows=[...this.rows.values()];const dead=rows.find(r=>r.legal.size===0);if(dead)return{kind:'dead',row:dead};
  const cmp=(a,b)=>a.generation-b.generation||a.legal.size-b.legal.size||a.key.localeCompare(b.key);const forced=rows.filter(r=>r.legal.size===1).sort(cmp);if(forced.length)return{kind:'forced',row:forced[0]};rows.sort(cmp);return rows.length?{kind:'branch',row:rows[0]}:{kind:'complete'};
 }
 *search(){if(this.stopped||this.stats.attempts>=this.nodeLimit)return'unknown';const pick=this.choice();this.lastChoice={kind:pick.kind,key:pick.row?.key,generation:pick.row?.generation,degree:pick.row?.legal.size};yield{type:pick.kind};if(pick.kind==='dead')return false;
  if(this.placed.length>this.bestViable.length)this.bestViable=this.placed.map(p=>({...p,translation:[...p.translation]}));
  if(this.placed.length>=this.target||pick.kind==='complete')return'checkpoint';
  const options=[...pick.row.legal].map(id=>{const c=this.pool.get(id);let fills=0,contacts=0;for(const e of c.corners){const p=this.points.get(e.key);if(p){contacts++;if(p.total+e.weight===12)fills++;}}return{c,score:fills*100+contacts,tie:this.random()};}).sort((a,b)=>b.score-a.score||a.tie-b.tie);
  if(pick.kind==='branch')this.stats.branches++;
  for(const{c}of options){if(this.stopped||this.stats.attempts>=this.nodeLimit)return'unknown';if(this.reason(c))continue;this.stats.attempts++;if(pick.kind==='forced')this.stats.forced++;
   const generation=1+Math.min(...c.corners.flatMap(e=>this.points.has(e.key)?[this.points.get(e.key).generation]:[]));const d=this.apply(c,generation);yield{type:'placement'};
   const result=yield* this.search();if(result==='checkpoint')return result;this.undo(d);this.stats.backtracks++;yield{type:'rollback'};if(result==='unknown')return result;
  }return false;
 }
 step(){const r=this.iterator.next();if(r.done){this.status=r.value==='checkpoint'?'consistent finite point patch':r.value===false?'exhausted rooted search':'unknown';return{done:true,status:this.status};}this.status='searching';return{done:false,...r.value};}
 snapshot(placements=this.placed){return{version:VERSION,branch:this.model.branch,support:this.model.support,coordinateScale:this.model.coordinateScale,status:this.status,target:this.target,nodeLimit:this.nodeLimit,placements:placements.map(({orientation,translation,generation})=>({orientation,translation,generation})),stats:{...this.stats,candidates:this.pool.size,frontierPoints:this.rows.size,pointNodes:this.points.size},choice:this.lastChoice,bestTiles:this.bestViable.length};}
 fingerprint(){return JSON.stringify({points:[...this.points].sort(),rows:[...this.rows].sort().map(([k,r])=>[k,r.generation,[...r.legal].sort()]),used:[...this.used].sort(),validity:[...this.validity].sort()});}
}

