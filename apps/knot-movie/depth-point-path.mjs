// Resumable bounded DFS over opaque point-valued move edges. Declared path
// adaptation, not the reference volume-tiling scheduler. One complete node
// expansion per yield allows fair scheduling across independent goal contexts.
export function* depthPointSteps(provider,{maxDepth=4,nodeCap=20000,stateCap=200000,seed=31,shouldStop=()=>false,allowNode=()=>true,allowState=()=>true}={}){
 if(!Number.isInteger(maxDepth)||maxDepth<0||!Number.isInteger(nodeCap)||nodeCap<0||!Number.isInteger(stateCap)||stateCap<1)throw Error('Invalid depth search bounds.');
 const stats={nodes:0,attempts:0,forced:0,branches:0,graphBuilds:0,peakIncidences:0,generatedStates:0,generatedEdges:0,domainCacheHits:0,rawCandidates:0,markingEliminations:0,authorRejections:0,markingVersions:0,replayedDomains:0,peakFrontier:0,extensionEliminations:0,extensionGraphBuilds:0,extensionVersions:0,extensionCandidateCount:0,deadEnds:0,baseLegalCandidates:0,availableCandidates:0,branchOptions:0,dominatedStates:0,horizonLeaves:0};
 const domains=new Map(),bestDepth=new Map();let version=provider.version(),randomState=seed>>>0;
 const mismatch=(c,b)=>[...c.m].some(([p,v])=>b.has(p)&&b.get(p)!==v);
 function refresh(d){stats.graphBuilds++;d.forward=new Map([[d.point,[]]]);d.reverse=new Map();for(const e of d.accepted){const c=provider.decorate(e.raw);if(mismatch(c,d.boundary))throw Error('Markings reject an accepted prefix edge.');d.forward.get(d.point).push(e.id);d.reverse.set(e.id,[d.point]);}stats.peakIncidences=Math.max(stats.peakIncidences,d.reverse.size);}
 function sync(){if(provider.version()===version)return;version=provider.version();stats.markingVersions=version;for(const d of domains.values()){refresh(d);stats.replayedDomains++;}}
 function domain(key){
  sync();if(domains.has(key)){stats.domainCacheHits++;return domains.get(key);}
  const raw=provider.domain(key);if(raw.complete!==true)return{unknown:true,reason:raw.reason||'incomplete-candidate-domain'};
  const d={point:raw.point,boundary:raw.boundary,accepted:[]};stats.rawCandidates+=raw.candidates.length;
  for(const entry of raw.candidates){
   if(shouldStop())return{unknown:true,reason:'search-time-budget'};
   const c=provider.decorate(entry);if(mismatch(c,d.boundary)){stats.markingEliminations++;continue;}
   const r=provider.resolve(entry);stats.attempts++;
   if(r?.unknown)return{unknown:true,reason:r.reason};
   if(!r){stats.authorRejections++;provider.observeRejected?.(entry);sync();continue;}
   if(c.t.size!==1||c.t.get(d.point)!==1)throw Error('Move must cover its one complete choice obligation.');
   d.accepted.push({raw:entry,id:c.id,destination:r.key});
  }
  refresh(d);domains.set(key,d);return d;
 }
 function* visit(key,depth,path){
  if(shouldStop())return{status:'unknown',reason:'search-time-budget'};
  if(key===provider.targetKey)return{status:'equivalent',path:[...path],distance:path.length};
  if(bestDepth.has(key)&&bestDepth.get(key)<=depth){stats.dominatedStates++;return null;}
  if(!bestDepth.has(key)){if(bestDepth.size>=stateCap||!allowState(stats.generatedStates))return{status:'unknown',reason:'search-state-budget'};stats.generatedStates++;}
  bestDepth.set(key,depth);stats.peakFrontier=Math.max(stats.peakFrontier,path.length+1);
  if(depth>=maxDepth){stats.horizonLeaves++;return null;}
  if(stats.nodes>=nodeCap||!allowNode(stats.nodes))return{status:'unknown',reason:'search-node-budget'};
  stats.nodes++;const d=domain(key);if(d.unknown)return{status:'unknown',reason:d.reason};
  let options=[...d.accepted];stats.baseLegalCandidates+=options.length;
  if(provider.extensionDomain){
   const marked=provider.extensionDomain(options,{targetKey:provider.targetKey,remaining:maxDepth-depth-1});
   if(marked.complete!==true)return{status:'unknown',reason:marked.reason||'incomplete-extension-domain'};
   const edges=new Map(options.map(e=>[e.id,e])),ids=new Set(edges.keys());
   if(marked.candidates.length!==options.length||new Set(marked.candidates.map(c=>c.id)).size!==ids.size||marked.candidates.some(c=>!ids.has(c.id)||c.t.size!==1||c.t.get(d.point)!==1))throw Error('Extension markings changed the complete candidate universe.');
   const forward=new Map([[d.point,[]]]),reverse=new Map(),kept=[];
   for(const c of marked.candidates){stats.extensionCandidateCount++;if(mismatch(c,marked.boundary)){stats.extensionEliminations++;continue;}forward.get(d.point).push(c.id);reverse.set(c.id,[d.point]);kept.push(edges.get(c.id));}
   stats.extensionGraphBuilds++;stats.extensionVersions=marked.version;stats.peakIncidences=Math.max(stats.peakIncidences,reverse.size);options=kept;
  }
  if(shouldStop())return{status:'unknown',reason:'search-time-budget'};
  stats.availableCandidates+=options.length;if(options.length>1){stats.branches++;stats.branchOptions+=options.length;}else if(options.length===1)stats.forced++;else stats.deadEnds++;
  for(let i=options.length-1;i>0;i--){randomState=(1664525*randomState+1013904223)>>>0;const j=Math.floor(randomState/4294967296*(i+1));[options[i],options[j]]=[options[j],options[i]];}
  yield{status:'running',stats}; // No degree/forced claim preceded exhaustion.
  sync();
  for(const e of options){stats.generatedEdges++;const r=yield* visit(e.destination,depth+1,[...path,e.id]);if(r)return r;}
  return null;
 }
 const result=yield* visit(provider.sourceKey,0,[]);
 return{...(result||{status:'exhausted-finite-search'}),stats};
}
export function depthPointPath(provider,options={}){const steps=depthPointSteps(provider,options);let r;do{r=steps.next();}while(!r.done);return r.value;}
