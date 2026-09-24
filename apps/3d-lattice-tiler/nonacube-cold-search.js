// Research driver: no learned assignments or obstruction catalogue as input.
import {CoronaGraph,pointKey,placementKey,allowedTranslation} from './corona-graph.js';
export function coldNonacubeModel(){
  return {capacity:8,placementDomain:{kind:'scaled_cubic',translationStep:2},orientations:[[0,1],[0,2],[1,2]].map(axes=>{
    const voxels=[[0,0,0]];for(const a of axes)for(const d of [-2,-1,1,2]){const p=[0,0,0];p[a]=d;voxels.push(p);}
    const weights=new Map();for(const v of voxels){weights.set(pointKey(v.map(x=>2*x)),8);for(const x of [-1,1])for(const y of [-1,1])for(const z of [-1,1]){const p=v.map((n,i)=>2*n+[x,y,z][i]),k=pointKey(p);weights.set(k,(weights.get(k)??0)+1);}}
    return {voxels,cells:[...weights].map(([k,weight])=>({pos:k.split(',').map(Number),weight}))};
  })};
}
export function graphFor(model,fixed){const graph=new CoronaGraph(model,{fixed,retainBranchCaches:false,dependencyLimit:2000000});for(const s of fixed)graph.apply(s,{root:true});return graph;}
export function graphSummary(graph){const candidates=new Set();let edges=0;const points=[...graph.active].map(k=>{const p=graph.points.get(k);for(const c of p.incident)if(c.valid){candidates.add(c.id);edges++;}return {point:p.pos,total:graph.totals.get(k),degree:p.degree};});return {points,candidates:candidates.size,edges};}
export function forcedClosure(model,fixed,{limit=100}={}){
  const graph=graphFor(model,fixed),forced=[];
  for(let i=0;i<=limit;i++){const s=graph.schedule();if(s.kind!=='forced')return {status:s.kind,point:s.point?.pos??null,forced,summary:graphSummary(graph)};if(i===limit)return {status:'unknown',forced,reason:'forced propagation budget'};const c=[...s.point.incident].find(c=>c.valid);forced.push({point:s.point.pos,placement:{oi:c.oi,translation:c.translation}});graph.apply(c);}
}
export function coldWalk(model,{seed=2,limit=100}={}){
  let state=seed>>>0;if(!state)throw Error('Nonzero PRNG seed required');const random=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/2**32;};
  const graph=graphFor(model,[{oi:0,translation:[0,0,0]}]),birth=new Map([...graph.active].map(k=>[k,0])),trace=[];
  for(let i=0;i<=limit;i++){
    let dead=null,forced=null,branch=null;
    for(const k of graph.active){const p=graph.points.get(k);if(!p.degree){dead=p;break;}if(p.degree===1)forced??=p;if(!branch||birth.get(k)<birth.get(branch.k))branch=p;}
    if(dead)return {seed,status:'dead',fixed:graph.descriptors(),deadPoint:dead.pos,trace};
    if(!branch)return {seed,status:'closed',fixed:graph.descriptors(),trace};
    if(i===limit)return {seed,status:'unknown',reason:'placement budget',fixed:graph.descriptors(),trace};
    const p=forced??branch,options=[...p.incident].filter(c=>c.valid),c=options[Math.floor(random()*options.length)];
    trace.push({kind:forced?'forced':'branch',point:p.pos,birth:birth.get(p.k),degree:p.degree,placement:{oi:c.oi,translation:[...c.translation]}});
    graph.apply(c);for(const k of graph.active)if(!birth.has(k))birth.set(k,i+1);
  }
}
export function minimizeFailure(model,walk){
  let fixed=[...walk.fixed];const q=walk.deadPoint,tests=[],distance=s=>Math.max(...s.translation.map((x,i)=>Math.abs(x-q[i])));
  // Repeat passes: minimality of bounded forced propagation is not assumed
  // monotone. Unknown trials are never treated as failures.
  let changed=true;while(changed){changed=false;for(const s of [...fixed].sort((a,b)=>distance(b)-distance(a))){const trial=fixed.filter(t=>t!==s),result=forcedClosure(model,trial),removed=result.status==='dead';tests.push({tile:s,remainingBefore:fixed.length,status:result.status,removed,point:result.point??null,forced:result.forced});if(removed){fixed=trial;changed=true;}}}
  const result=forcedClosure(model,fixed);return {fixed,deadPoint:result.point,forced:result.forced,tests};
}
export function rawCoverCertificate(model,fixed,point){
  const totals=new Map();for(const s of fixed)for(const c of model.orientations[s.oi].cells){const k=pointKey(c.pos.map((x,i)=>x+s.translation[i]));totals.set(k,(totals.get(k)??0)+c.weight);}
  const rows=new Map();for(let oi=0;oi<model.orientations.length;oi++)for(const a of model.orientations[oi].cells){const translation=point.map((x,i)=>x-a.pos[i]),s={oi,translation};if(!allowedTranslation(model,translation)||rows.has(placementKey(s)))continue;const blockers=[];
    for(const c of model.orientations[oi].cells){const pos=c.pos.map((x,i)=>x+translation[i]),total=totals.get(pointKey(pos))??0;if(total+c.weight>model.capacity)blockers.push({point:pos,total,contribution:c.weight});}
    rows.set(placementKey(s),{placement:s,blockers});
  }return [...rows.values()];
}
