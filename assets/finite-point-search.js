/** Exact finite point-capacity engine. Required points include untouched zero
 * points. Integer units encode rational weights. All explicit root obligations
 * have generation zero. Mark-only dependencies are independent of occupancy.
 */
import {PointMarkingState,markingValueKey} from './exact-point-marking-state.js';
import {chooseObligation} from './polyhedral-exact-search.js';
export class FinitePointSearch{
 constructor(model,{target=60,seed=4,budget=10000}={}){
  this.model=model;this.config={system:model.id,target,seed,budget};this.capacity=BigInt(model.capacity);this.trail=[];this.frames=[];this.placed=new Map();this.candidates=new Map();this.frontier=new Map();this.points=new Map();this.dependencies=new Map();this.pointMarkings=new PointMarkingState({set:(m,k,v)=>this.set(m,k,v),add:(s,k)=>this.add(s,k)});this.state='ready';this.complete=true;this.events=[];this.tree=[];this.lastEvent={type:'seed'};this.stats={attempts:0,accepted:0,forced:0,branches:0,backtracks:0,eliminatedOverlap:0,eliminatedContact:0,eliminatedMarking:0,eliminatedRules:0,eliminatedLearned:0,checks:0,elapsedMs:0,maxTiles:1};
  for(const key of model.required){const point={key,total:0n,generation:0,candidates:new Set()};this.points.set(key,point);this.frontier.set(key,point);}
  for(const tile of model.placements){if(this.candidates.has(tile.id))throw Error('Duplicate point placement identity');const r={tile,legal:true,excluded:false};this.candidates.set(tile.id,r);for(const p of tile.occupancy){if(!this.points.has(p.key)||p.weight<=0n||p.weight>this.capacity)throw Error('Invalid point contribution');if(!this.dependencies.has(p.key))this.dependencies.set(p.key,new Set());this.dependencies.get(p.key).add(tile.id);this.frontier.get(p.key).candidates.add(tile.id);}this.pointMarkings.register(tile);}
  const root=model.placements.find(t=>t.id===model.seedId)||model.placements[0];if(!root)throw Error('No root placement');this.seed=root;this.apply(root,0);this.trail=[];
 }
 set(m,k,v){const had=m.has(k),old=m.get(k);this.trail.push(()=>had?m.set(k,old):m.delete(k));m.set(k,v);}
 put(obj,key,value){const old=obj[key];this.trail.push(()=>obj[key]=old);obj[key]=value;}
 add(s,k){if(s.has(k))return;this.trail.push(()=>s.delete(k));s.add(k);}
 del(m,k){if(!m.has(k))return;const old=m.get(k);this.trail.push(()=>m.set(k,old));m.delete(k);}
 drop(s,k){if(!s.has(k))return;this.trail.push(()=>s.add(k));s.delete(k);}
 undo(n){while(this.trail.length>n)this.trail.pop()();}
 legal(tile){this.stats.checks++;return !this.placed.has(tile.id)&&this.pointMarkings.compatible(tile)&&tile.occupancy.every(p=>this.points.get(p.key).total+p.weight<=this.capacity);}
 invalidate(r,reason){if(!r.legal)return;this.trail.push(()=>r.legal=true);r.legal=false;for(const p of r.tile.occupancy){const point=this.frontier.get(p.key);if(point)this.drop(point.candidates,r.tile.id);}if(reason==='failed-child'){const old=r.excluded;this.trail.push(()=>r.excluded=old);r.excluded=true;}else this.stats[reason==='marking'?'eliminatedMarking':'eliminatedOverlap']++;}
 apply(tile,rootGeneration=null){
  if(!this.legal(tile))throw Error('Illegal point placement');const touched=tile.occupancy.map(p=>this.frontier.get(p.key)).filter(Boolean),generation=rootGeneration??1+Math.min(...touched.map(p=>p.generation));this.set(this.placed,tile.id,{tile,generation});this.pointMarkings.assign(tile);
  const changed=new Set(this.pointMarkings.affected(tile));for(const p of tile.occupancy){const point=this.points.get(p.key);this.put(point,'total',point.total+p.weight);for(const id of this.dependencies.get(p.key)||[])changed.add(id);}
  for(const id of changed){const r=this.candidates.get(id);if(r.legal&&!this.legal(r.tile))this.invalidate(r,!this.pointMarkings.compatible(r.tile)?'marking':'capacity');}
  for(const p of tile.occupancy)if(this.points.get(p.key).total===this.capacity)this.del(this.frontier,p.key);
  return generation;
 }
 step(){
  if(['complete','checkpoint','budget','exhausted'].includes(this.state))return this.lastEvent;const started=performance.now(),choice=chooseObligation(this.frontier);
  if(choice?.kind==='dead'){const frame=this.frames.pop();if(!frame){this.state='exhausted';this.lastEvent={type:'exhausted',reason:'complete finite point search exhausted'};}else{this.undo(frame.before);this.invalidate(this.candidates.get(frame.id),'failed-child');this.stats.backtracks++;this.lastEvent={type:'remove',tile:frame.id,reason:'global dead point'};}}
  else if(!choice){this.verify();this.state='complete';this.lastEvent={type:'complete',reason:this.model.completion};}
  else if(this.placed.size>=this.config.target){this.state='checkpoint';this.lastEvent={type:'checkpoint',reason:'finite consistent point assignment with viable frontier'};}
  else if(this.stats.attempts>=this.config.budget){this.state='budget';this.lastEvent={type:'budget',reason:'attempt limit; result unknown'};}
  else{
   const ids=[...choice.point.candidates].sort(),offset=this.config.seed%ids.length,id=ids[offset],before=this.trail.length;this.stats.attempts++;const generation=this.apply(this.candidates.get(id).tile);this.frames.push({id,before});this.stats.accepted++;this.stats[choice.kind==='forced'?'forced':'branches']++;this.stats.maxTiles=Math.max(this.stats.maxTiles,this.placed.size);this.state='running';this.lastEvent={type:'add',tile:id,generation,forced:choice.kind==='forced',domain:ids.length};
  }
  this.stats.elapsedMs+=performance.now()-started;this.events.push({...this.lastEvent,tiles:this.placed.size,depth:this.frames.length});return this.lastEvent;
 }
 summary(){const live=new Set();let incidences=0;for(const p of this.frontier.values())for(const id of p.candidates){live.add(id);incidences++;}return {state:this.state,tiles:this.placed.size,frontier:this.frontier.size,candidates:live.size,incidences,dead:[...this.frontier.values()].filter(p=>!p.candidates.size).length,domainsComplete:true,required:this.points.size,markingPoints:this.pointMarkings.pointCount,markingComponents:this.pointMarkings.componentCount,...this.stats};}
 verify(){const totals=new Map([...this.points.keys()].map(k=>[k,0n])),marks=new Map();for(const {tile}of this.placed.values()){for(const p of tile.occupancy)totals.set(p.key,totals.get(p.key)+p.weight);for(const m of tile.pointMarkings||[])for(const [c,v]of Object.entries(m.components)){const key=m.point.map(x=>x.key()).join(';')+':'+c;if(marks.has(key)&&marks.get(key)!==markingValueKey(v))throw Error('Independent marking replay failed');marks.set(key,markingValueKey(v));}}if([...totals.values()].some(v=>v!==this.capacity))throw Error('Finite target capacity replay failed');return true;}
 inspect(){return {points:[...this.points].map(([k,p])=>[k,String(p.total)]).sort(),placed:[...this.placed].map(([k,r])=>[k,r.generation]).sort(),frontier:[...this.frontier].map(([k,p])=>[k,[...p.candidates].sort()]).sort(),candidates:[...this.candidates].map(([k,r])=>[k,r.legal,r.excluded]).sort(),marks:this.pointMarkings.inspect()};}
 export(){return {format:'gcts-finite-point-control-v1',system:this.model.id,scope:this.model.scope,domain:this.model.domain,capacityUnits:String(this.capacity),config:this.config,result:this.state==='complete'?this.model.completion:this.state==='checkpoint'?'consistent finite partial point assignment':'unknown',stats:this.summary(),required:[...this.points].map(([k,p])=>[k,String(p.total)]).sort(),tiles:[...this.placed.values()].map(({tile,generation})=>({kind:tile.kind,vertices:tile.vertices.map(p=>p.map(x=>x.toJSON())),faces:tile.faces,occupancy:tile.occupancy.map(p=>[p.key,String(p.weight)]),pointMarkings:tile.pointMarkings,generation})),events:this.events};}
}
