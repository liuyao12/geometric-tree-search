// Exact finite point-window engine. No face, volume, periodic, or catalog rule
// participates in legality. All reversible changes share one trail.
export const key=p=>p.join(',');
const plus=(a,b)=>a.map((x,i)=>x+b[i]);
const gcd=(a,b)=>b?gcd(b,a%b):a;
const hash=s=>{let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0;};
export class PointGraph {
  constructor(model,{candidateLimit=180000}={}) {
    this.model=model;this.points=new Map();this.candidates=[];this.dependencies=new Map();this.markDependencies=new Map();this.totals=new Map();this.section=new Map();this.selected=[];this.trail=[];this.edges=0;
    if(!Number.isSafeInteger(model.capacity)||model.capacity<1)throw Error('Invalid capacity');
    for(const o of model.orientations){
      if(!o.cells.length||new Set(o.cells.map(c=>key(c.pos))).size!==o.cells.length||o.cells.some(c=>!Number.isSafeInteger(c.weight)||c.weight<=0||c.weight>model.capacity||c.pos.length!==3||c.pos.some(x=>!Number.isSafeInteger(x))))throw Error('Invalid exact point model');
      if(new Set((o.marks??[]).map(m=>key(m.pos))).size!==(o.marks??[]).length)throw Error('Duplicate marking point');
    }
    for(const p of model.required)this.points.set(key(p.pos),{pos:p.pos,generation:p.generation??0,incident:[],degree:0});
    const unique=new Map();
    for(const p of this.points.values())for(let oi=0;oi<model.orientations.length;oi++){
      const o=model.orientations[oi];
      for(const a of o.cells){
        const translation=p.pos.map((x,i)=>x-a.pos[i]);const id=`${oi}@${translation}`;
        if(unique.has(id))continue;
        if(this.candidates.length>=candidateLimit){const e=Error('Complete graph exceeds the 180,000-candidate memory budget. Reduce the window.');e.kind='resource_limit';throw e;}
        const c={id,oi,translation,valid:true,selected:false,cells:o.cells.map(q=>({k:key(plus(q.pos,translation)),weight:q.weight})),marks:(o.marks??[]).map(m=>({k:key(plus(m.pos,translation)),value:JSON.stringify(m.value)})),points:[]};
        unique.set(id,c);this.candidates.push(c);
        for(const cell of c.cells){
          if(!this.dependencies.has(cell.k))this.dependencies.set(cell.k,new Set());this.dependencies.get(cell.k).add(c);
          const q=this.points.get(cell.k);if(q){q.incident.push(c);q.degree++;c.points.push(q);this.edges++;}
        }
        for(const m of c.marks){if(!this.markDependencies.has(m.k))this.markDependencies.set(m.k,new Set());this.markDependencies.get(m.k).add(c);}
      }
    }
  }
  legal(c){return !c.selected&&c.cells.every(p=>(this.totals.get(p.k)??0)+p.weight<=this.model.capacity)&&c.marks.every(m=>!this.section.has(m.k)||this.section.get(m.k).value===m.value);}
  disable(c){if(!c.valid)return;this.trail.push(['valid',c]);c.valid=false;for(const p of c.points)p.degree--;}
  apply(c){
    if(!c.valid||!this.legal(c))throw Error('Invalid graph placement');
    const mark=this.trail.length;
    this.trail.push(['selected',c]);c.selected=true;this.selected.push(c);this.disable(c);
    const incident=c.cells.map(p=>this.points.get(p.k)?.generation).filter(x=>x!==undefined);
    c.generation=incident.length?1+Math.min(...incident):0;
    const affected=new Set();
    for(const p of c.cells){this.trail.push(['total',p.k,this.totals.get(p.k)]);this.totals.set(p.k,(this.totals.get(p.k)??0)+p.weight);for(const n of this.dependencies.get(p.k)??[])affected.add(n);}
    for(const m of c.marks){const prev=this.section.get(m.k);this.trail.push(['mark',m.k,prev]);this.section.set(m.k,{value:m.value,count:(prev?.count??0)+1});for(const n of this.markDependencies.get(m.k)??[])affected.add(n);}
    for(const n of affected)if(n.valid&&!this.legal(n))this.disable(n);
    return mark;
  }
  rollback(mark){while(this.trail.length>mark){const [kind,item,old]=this.trail.pop();if(kind==='valid'){item.valid=true;for(const p of item.points)p.degree++;}else if(kind==='selected'){item.selected=false;delete item.generation;this.selected.pop();}else{const map=kind==='total'?this.totals:this.section;if(old===undefined)map.delete(item);else map.set(item,old);}}}
  schedule(){
    let forced=null,branch=null,remaining=0;
    for(const [k,p] of this.points){
      if(this.totals.get(k)===this.model.capacity)continue;remaining++;
      if(!p.degree)return {kind:'dead',point:p,remaining};
      if(p.degree===1)forced??=p;
      if(!branch||p.generation<branch.generation||(p.generation===branch.generation&&p.degree<branch.degree))branch=p;
    }
    return {kind:!remaining?'solved':forced?'forced':'branch',point:forced??branch,remaining};
  }
  domain(p){return p.incident.filter(c=>c.valid);}
  digest(){return JSON.stringify({totals:[...this.totals].sort(),marks:[...this.section].sort(),selected:this.selected.map(c=>c.id),valid:this.candidates.map(c=>c.valid),degrees:[...this.points.values()].map(p=>p.degree)});}
  verifyDomains(){for(const c of this.candidates)if(c.valid!==this.legal(c))throw Error('Exhaustive domain mismatch');return true;}
}

// Independent certificate replay: no graph, caches, scheduler, or learned data.
export function verify(model,placements){
  if(!Number.isSafeInteger(model.capacity)||model.capacity<1||!Array.isArray(model.required)||!model.required.length||!Array.isArray(model.orientations))return {ok:false,reason:'invalid model'};
  const exactPoint=p=>Array.isArray(p)&&p.length===3&&p.every(Number.isSafeInteger);
  if(model.required.some(p=>!exactPoint(p.pos))||new Set(model.required.map(p=>key(p.pos))).size!==model.required.length)return {ok:false,reason:'invalid target'};
  for(const o of model.orientations){
    if(!Array.isArray(o.cells)||!o.cells.length||o.cells.some(c=>!exactPoint(c.pos)||!Number.isSafeInteger(c.weight)||c.weight<=0||c.weight>model.capacity)||new Set(o.cells.map(c=>key(c.pos))).size!==o.cells.length)return {ok:false,reason:'invalid support'};
    if((o.marks??[]).some(m=>!exactPoint(m.pos)||m.value===undefined)||new Set((o.marks??[]).map(m=>key(m.pos))).size!==(o.marks??[]).length)return {ok:false,reason:'invalid marking'};
  }
  const totals=new Map(),section=new Map(),ids=new Set();
  for(const p of placements){
    const o=model.orientations[p.oi];if(!o||p.translation.length!==3||p.translation.some(x=>!Number.isSafeInteger(x)))return {ok:false,reason:'invalid placement'};
    const id=`${p.oi}@${p.translation}`;if(ids.has(id))return {ok:false,reason:'duplicate placement'};ids.add(id);
    if(!o.cells.some(c=>model.required.some(q=>key(plus(c.pos,p.translation))===key(q.pos))))return {ok:false,reason:'placement misses target'};
    for(const c of o.cells){const k=key(plus(c.pos,p.translation)),v=(totals.get(k)??0)+c.weight;if(v>model.capacity)return {ok:false,reason:'capacity exceeded'};totals.set(k,v);}
    for(const m of o.marks??[]){const k=key(plus(m.pos,p.translation)),v=JSON.stringify(m.value);if(section.has(k)&&section.get(k)!==v)return {ok:false,reason:'marking disagreement'};section.set(k,v);}
  }
  const covered=model.required.filter(p=>totals.get(key(p.pos))===model.capacity).length;
  return {ok:covered===model.required.length,covered,required:model.required.length,reason:covered===model.required.length?'finite exact point window':'incomplete window'};
}

export async function* search(model,config={}) {
  const started=performance.now(),mode=config.mode??'free',gcts=['gcts','both'].includes(mode),rl=['rl','both'].includes(mode);
  const stats={attempts:0,accepted:0,forced:0,branches:0,backtracks:0,capacityCuts:0,lookaheadCuts:0,probes:0,clusterProposals:0,clusterValidated:0,clusterUses:0,learningMs:0,graphMs:0,peakTrail:0};
  const graph=new PointGraph(model);stats.graphMs=performance.now()-started;
  const seed=config.seed??1,library=new Map(),limit=config.timeMs??10000,nodeLimit=config.nodes??10000;
  let stopReason=null,best=[],lastEmit=0;
  const expired=()=>{if(performance.now()-started>=limit)stopReason='time budget';else if(stats.attempts>=nodeLimit)stopReason='attempt budget';return !!stopReason;};
  const descriptors=()=>graph.selected.map(c=>({oi:c.oi,translation:c.translation.slice(),generation:c.generation}));
  const metric=()=>({...stats,elapsedMs:performance.now()-started,candidates:graph.candidates.length,edges:graph.edges,points:graph.points.size,clusters:library.size,memoryEstimateBytes:graph.candidates.reduce((s,c)=>s+160+c.cells.length*40+c.marks.length*40,0)+graph.edges*8+stats.peakTrail*24});
  function residualDead(){
    for(const [k,p] of graph.points){const d=model.capacity-(graph.totals.get(k)??0);if(!d)continue;let sum=0,g=0;
      for(const c of p.incident)if(c.valid){const w=c.cells.find(q=>q.k===k).weight;sum+=w;g=gcd(g,w);}
      if(sum<d||!g||d%g)return true;
    }return false;
  }
  function filter(){
    if(residualDead()){stats.capacityCuts++;return;}
    let s=graph.schedule();if(s.kind!=='branch')return;
    // A bounded subset affects pruning strength only, never the base universe.
    for(const c of graph.domain(s.point).slice(0,8)){
      if(expired())return;const mark=graph.apply(c);stats.probes++;
      let next=graph.schedule(),steps=0;
      while(next.kind==='forced'&&steps++<3){graph.apply(graph.domain(next.point)[0]);next=graph.schedule();}
      const dead=next.kind==='dead'||residualDead();graph.rollback(mark);
      if(dead){graph.disable(c);stats.lookaheadCuts++;}
    }
  }
  function proposals(moves){
    const start=performance.now(),ranked=[];
    for(const first of moves.slice(0,4)){
      if(expired())break;
      const mark=graph.trail.length,expansion=[];let next=first;
      for(let i=0;i<3&&next;i++){
        graph.apply(next);expansion.push({oi:next.oi,translation:next.translation.map((x,j)=>x-first.translation[j])});
        const s=graph.schedule();if(s.kind==='dead')break;
        next=s.point?graph.domain(s.point).sort((a,b)=>hash(`${seed}:${a.id}`)-hash(`${seed}:${b.id}`))[0]:null;
      }
      stats.clusterProposals++;
      const s=graph.schedule(),signature=JSON.stringify(expansion);
      const covered=model.required.length-s.remaining;
      if(s.kind!=='dead'){
        stats.clusterValidated++;let record=library.get(signature);
        if(!record){record={expansion,visits:0,value:0,seed,source:'online scheduler-valid rollout'};if(library.size<512)library.set(signature,record);}
        ranked.push({first,record,score:covered+(config.learnReturns===false?0:record.value)});
      }
      graph.rollback(mark);
    }
    ranked.sort((a,b)=>b.score-a.score);stats.learningMs+=performance.now()-start;
    return ranked[0];
  }
  async function* visit(depth){
    if(expired())return false;
    if(depth>1024){stopReason='depth budget';return false;}
    const mark=graph.trail.length;
    let s=graph.schedule(); // Global dead always precedes forced or goal.
    if(s.kind==='dead'){graph.rollback(mark);return false;}
    if(gcts){filter();s=graph.schedule();if(residualDead()){graph.rollback(mark);return false;}}
    if(expired()){graph.rollback(mark);return false;}
    if(s.kind==='solved')return true;
    if(s.kind==='dead'){graph.rollback(mark);return false;}
    let moves=graph.domain(s.point).sort((a,b)=>hash(`${seed}:${a.id}`)-hash(`${seed}:${b.id}`));
    let proposal=null;
    if(s.kind==='branch'){stats.branches++;if(rl){proposal=proposals(moves);if(proposal){moves=[proposal.first,...moves.filter(c=>c!==proposal.first)];stats.clusterUses++;}}}
    for(const c of moves){
      if(expired())break;
      stats.attempts++;stats.accepted++;if(s.kind==='forced')stats.forced++;
      const child=graph.apply(c);stats.peakTrail=Math.max(stats.peakTrail,graph.trail.length);
      const covered=model.required.filter(p=>graph.totals.get(key(p.pos))===model.capacity).length;
      if(covered>(best.covered??-1)){best=descriptors();best.covered=covered;}
      if(performance.now()-lastEmit>100){lastEmit=performance.now();yield {type:'progress',placements:descriptors(),covered,stats:metric()};await new Promise(r=>setTimeout(r,0));}
      const won=yield* visit(depth+1);
      if(proposal&&c===proposal.first){const start=performance.now(),r=proposal.record;r.visits++;r.value+=( (won?model.required.length:-1)-r.value)/r.visits;stats.learningMs+=performance.now()-start;}
      if(won)return true;
      graph.rollback(child);stats.backtracks++;
      if(stopReason)break;
    }
    graph.rollback(mark);return false;
  }
  const won=yield* visit(0),placements=won?descriptors():Array.from(best);
  const verification=verify(model,placements);
  if(won&&!verification.ok)throw Error('Independent verification failed');
  yield {type:'result',mode,result:won?'finite_exact':stopReason?'unknown':'exhausted_finite',reason:stopReason,placements,verification,stats:metric(),clusters:[...library.values()],config,model};
}
