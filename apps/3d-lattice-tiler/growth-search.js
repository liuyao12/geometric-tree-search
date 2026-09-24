// Seed-based point growth, following the decision order in GCTS-I.html.
// The finite-window engine remains a separate, explicitly selected control.
import {CoronaGraph,pointKey,add,sub,placementKey,allowedTranslation,validatePointModel} from './corona-graph.js?v=20260921-vector-learning';
import {markingSlots} from './v2/search.js';
const slots=(model,p)=>markingSlots(model.orientations[p.oi].marks).map(m=>({k:`${pointKey(add(m.pos,p.translation))}|${m.component}`,value:JSON.stringify(m.value)}));
export class GrowthGraph extends CoronaGraph {
 constructor(model,options={}){
  super(model,{retainBranchCaches:false,candidateLimit:300000,dependencyLimit:4000000,...options});
  this.section=new Map();this.markDependencies=new Map();this.markingCuts=0;
  for(const o of model.orientations){const fields=markingSlots(o.marks),seen=new Set();for(const m of fields){const k=`${pointKey(m.pos)}|${m.component}`;if(m.pos.length!==3||!m.pos.every(Number.isSafeInteger)||m.value===undefined||seen.has(k))throw Error('Invalid point marking');seen.add(k);}}
 }
 legal(c){return super.legal(c)&&(c.marks??[]).every(m=>!this.section.has(m.k)||this.section.get(m.k).value===m.value);}
 candidate(oi,translation){
  const c=super.candidate(oi,translation);if(!c||c.marks)return c;
  c.marks=slots(this.model,c);c.valid=this.legal(c);
  for(const m of c.marks){if(!this.markDependencies.has(m.k))this.markDependencies.set(m.k,new Set());this.markDependencies.get(m.k).add(c);}
  return c;
 }
 refreshMarks(keys){
  const affected=new Set();for(const k of keys)for(const c of this.markDependencies.get(k)??[])affected.add(c);
  for(const c of affected){const valid=this.legal(c);if(valid===c.valid)continue;if(!valid&&super.legal(c))this.markingCuts++;for(const p of c.points)p.degree+=valid?1:-1;c.valid=valid;}
 }
 apply(spec,options={}){
  const c=this.candidate(spec.oi,spec.translation);if(!c||!this.legal(c))throw Error('Illegal growth placement');const adjacent=c.cells.flatMap(p=>[...(this.generations.get(p.k)?.keys()??[])]);
  const generation=options.root?0:adjacent.length?1+Math.min(...adjacent):0;
  const undo=super.apply(spec,options);undo.marks=c.marks.map(m=>[m.k,this.section.get(m.k)]);
  c.generation=generation;
  for(const m of c.marks){const old=this.section.get(m.k);this.section.set(m.k,{value:m.value,count:(old?.count??0)+1});}
  this.refreshMarks(c.marks.map(m=>m.k));return undo;
 }
 rollback(undo){
  const c=this.selected.at(-1);for(const [k,old] of undo.marks){if(old)this.section.set(k,old);else this.section.delete(k);}
  super.rollback(undo);delete c.generation;this.refreshMarks(undo.marks.map(([k])=>k));
 }
 releaseCaches(sizes){
  for(const c of this.candidateOrder.slice(sizes[1]))for(const m of c.marks){const set=this.markDependencies.get(m.k);set.delete(c);if(!set.size)this.markDependencies.delete(m.k);}
  super.releaseCaches(sizes);
 }
 schedule(){
  const entries=[];
  for(const k of this.active){const p=this.points.get(k);if(!p.degree)return {kind:'dead',point:p};const layer=this.model.slab?p.pos.reduce((a,b)=>a+b,0)/3:0,rankPos=p.pos.map(x=>x-layer);entries.push({point:p,rankPos,rankKey:rankPos.join(','),generation:Math.min(...this.generations.get(k).keys())});}
  const order=(a,b)=>a.generation-b.generation||a.point.degree-b.point.degree||Math.max(...a.rankPos.map(Math.abs))-Math.max(...b.rankPos.map(Math.abs))||(this.totals.get(b.point.k)??0)-(this.totals.get(a.point.k)??0)||a.rankPos.reduce((s,x)=>s+Math.abs(x),0)-b.rankPos.reduce((s,x)=>s+Math.abs(x),0)||(a.rankKey<b.rankKey?-1:a.rankKey>b.rankKey?1:0);
  const forced=entries.filter(e=>e.point.degree===1).sort(order)[0],branch=entries.sort(order)[0];
  return {kind:forced?'forced':branch?'branch':'closed',point:(forced??branch)?.point,generation:(forced??branch)?.generation};
 }
 descriptors(){return this.selected.map(c=>({oi:c.oi,translation:[...c.translation],generation:c.generation}));}
}
export function orderGrowthCandidates(graph,point,random){
 return [...point.incident].filter(c=>c.valid).map(c=>{
  const coverage=c.cells.filter(p=>p.total>0).length,index=c.cells.findIndex(p=>p.k===point.k);
  return {c,fills:(graph.totals.get(point.k)??0)+c.weights[index]>=graph.model.capacity,degree:[...c.points].filter(p=>graph.active.has(p.k)).length,coverage,newPoints:c.cells.length-coverage,tie:random()};
 }).sort((a,b)=>Number(b.fills)-Number(a.fills)||b.degree-a.degree||b.coverage-a.coverage||b.newPoints-a.newPoints||a.tie-b.tie).map(e=>e.c);
}
// Independent replay: sum point weights, compare assigned components, and
// exhaustively enumerate candidates at every exposed point (including outside
// the view). Does not trust the graph, its cached degrees, or learned labels.
export function verifyGrowth(model,placements,{seed={oi:0,translation:[0,0,0]},frontier=true}={}){
 validatePointModel(model);const totals=new Map(),section=new Map(),used=new Set();
 for(const p of placements){
  const o=model.orientations[p.oi],id=placementKey(p);if(!o||used.has(id)||!allowedTranslation(model,p.translation))return {ok:false,reason:'invalid placement'};used.add(id);
  for(const c of o.cells){const k=pointKey(add(c.pos,p.translation)),n=(totals.get(k)??0)+c.weight;if(n>model.capacity)return {ok:false,reason:'capacity exceeded'};totals.set(k,n);}
  for(const m of slots(model,p)){if(section.has(m.k)&&section.get(m.k)!==m.value)return {ok:false,reason:'marking disagreement'};section.set(m.k,m.value);}
 }
 if(!used.has(placementKey(seed)))return {ok:false,reason:'missing root seed'};
 const exposed=[...totals].filter(([,n])=>n<model.capacity),dead=[];
 if(frontier)for(const [k] of exposed){
  const pos=k.split(',').map(Number);let viable=false;
  outer:for(let oi=0;oi<model.orientations.length;oi++)for(const a of model.orientations[oi].cells){
   const translation=sub(pos,a.pos),p={oi,translation};if(!allowedTranslation(model,translation)||used.has(placementKey(p)))continue;
   if(!model.orientations[oi].cells.every(c=>(totals.get(pointKey(add(c.pos,translation)))??0)+c.weight<=model.capacity))continue;
   if(!slots(model,p).every(m=>!section.has(m.k)||section.get(m.k)===m.value))continue;
   viable=true;break outer;
  }
  if(!viable)dead.push(pos);
 }
 return {ok:!dead.length,frontierViable:frontier?!dead.length:null,deadPoints:dead,frontierPoints:exposed.length,covered:totals.size-exposed.length,activePoints:totals.size,tiles:placements.length,reason:dead.length?'dead frontier':'consistent finite patch; infinite extension unproved'};
}
export async function* grow(model,config={}){
 const started=performance.now(),mode=config.mode??'free',seed=config.root??{oi:0,translation:[0,0,0]},target=Math.max(1,config.targetTiles??1000),limit=config.timeMs??120000;
 const stats={attempts:0,accepted:0,forced:0,branches:0,backtracks:0,capacityCuts:0,lookaheadCuts:0,clusterProposals:0,clusterValidated:0,clusterUses:0,learningMs:0,graphMs:0,peakTrail:0};
 const graph=new GrowthGraph(model,{fixed:[seed],candidateLimit:config.candidateLimit??300000,dependencyLimit:config.dependencyLimit??4000000});
 let rng=(config.seed??10)|0,reason=null,best=[],lastEmit=-Infinity;const random=()=>((rng=Math.imul(rng,1664525)+1013904223|0)>>>0)/4294967296;
 const library=new Map(),rl=['rl','both'].includes(mode);
 const expired=()=>{if(config.stop?.())reason='cancelled';else if(performance.now()-started>=limit)reason='time budget';else if(stats.attempts>=(config.nodes??1000000))reason='attempt budget';return !!reason;};
 const metric=()=>({...stats,elapsedMs:performance.now()-started,markingCuts:graph.markingCuts,candidates:graph.candidates.size,edges:[...graph.points.values()].reduce((n,p)=>n+p.incident.size,0),points:graph.totals.size,frontierPoints:graph.active.size,memoryEstimateBytes:graph.dependencyEntries*48+graph.candidates.size*200+[...graph.candidates.values()].reduce((n,c)=>n+(c.marks?.length??0)*48,0)+graph.section.size*48,searchProtocol:'seed-growth'});
 const frame=(type='progress',action='place',point=null)=>({type,action,point,mode,placements:graph.descriptors(),covered:graph.selected.length,frontier:[...graph.active].map(k=>({pos:graph.points.get(k).pos,generation:Math.min(...graph.generations.get(k).keys()),degree:graph.points.get(k).degree})),stats:metric()});
 function proposal(moves){
  const begun=performance.now(),ranked=[];
  for(const first of moves.slice(0,4)){
   if(expired())break;const undos=[],expansion=[];let next=first;
   try{
    for(let i=0;i<3&&next;i++){
     undos.push(graph.apply(next));expansion.push({oi:next.oi,translation:sub(next.translation,first.translation)});
     const s=graph.schedule();if(s.kind==='dead')break;next=s.point?orderGrowthCandidates(graph,s.point,random)[0]:null;
    }
    stats.clusterProposals++;const s=graph.schedule();
    if(s.kind!=='dead'){
     stats.clusterValidated++;const key=JSON.stringify(expansion);let record=library.get(key);
     if(!record){record={expansion,visits:0,value:0,source:'online growth scheduler-valid rollout'};if(library.size<512)library.set(key,record);}
     ranked.push({first,record,score:expansion.length+(config.learnReturns===false?0:record.value)});
    }
   }finally{for(const undo of undos.reverse())graph.rollback(undo);}
  }
  stats.learningMs+=performance.now()-begun;return ranked.sort((a,b)=>b.score-a.score)[0];
 }
 // Explicit DFS frames allow 1,000+ tiles without recursive generator stacks.
 const stack=[];let won=false;
 try{
  graph.apply(seed,{root:true});stats.graphMs=performance.now()-started;
  yield frame('progress','seed');
  let entering=true;
  while(true){
   if(expired())break;
   if(entering){
    const s=graph.schedule();if(config.audit)graph.audit();
    if(s.kind!=='dead'){
     if(graph.selected.length>best.length)best=graph.descriptors();
     if(graph.selected.length>=target||s.kind==='closed'){won=true;break;}
     let moves=orderGrowthCandidates(graph,s.point,random),pick=null;
     if(s.kind==='branch'){stats.branches++;if(rl){pick=proposal(moves);if(pick){moves=[pick.first,...moves.filter(c=>c!==pick.first)];stats.clusterUses++;}}}
     stack.push({moves,index:0,kind:s.kind,point:s.point.pos,pick,undo:null});
    }else if(config.trace||performance.now()-lastEmit>50){lastEmit=performance.now();yield frame('progress','dead',s.point.pos);await new Promise(r=>setTimeout(r,0));}
    entering=false;
   }
   let advance=false;
   while(stack.length&&!advance){
    const f=stack.at(-1);
    if(f.undo){graph.rollback(f.undo);f.undo=null;stats.backtracks++;if(config.trace||performance.now()-lastEmit>50){lastEmit=performance.now();yield frame('progress','backtrack');await new Promise(r=>setTimeout(r,0));}}
    if(f.index===f.moves.length){stack.pop();if(f.pick){const r=f.pick.record;r.visits++;r.value+=(-1-r.value)/r.visits;}continue;}
    if(expired())break;
    const c=f.moves[f.index++];f.undo=graph.apply(c);stats.attempts++;stats.accepted++;if(f.kind==='forced')stats.forced++;
    if(config.trace||performance.now()-lastEmit>50){lastEmit=performance.now();yield frame('progress',f.kind==='forced'?'forced':'place',f.point);await new Promise(r=>setTimeout(r,0));}
    advance=true;entering=true;
   }
   if(!advance)break;
  }
  if(won)for(const f of stack)if(f.pick){const r=f.pick.record;r.visits++;r.value+=(target-r.value)/r.visits;}
 }catch(e){if(e.kind!=='resource_limit')throw e;reason=e.message;}
 const placements=won?graph.descriptors():best.length?best:[seed],verificationStarted=performance.now();
 const verification=verifyGrowth(model,placements);stats.verificationMs=performance.now()-verificationStarted;
 if(won&&!verification.ok)throw Error('Independent growth verification failed');
 yield {type:'result',mode,result:won?(placements.length>=target?'growth_checkpoint':'closed_patch'):reason?'unknown':config.learnedRestriction?'exhausted_marked':'exhausted_seed',reason,placements,verification,covered:placements.length,stats:metric(),clusters:[...library.values()],config,model,searchProtocol:'seed-growth'};
}
