// Generic, bidirectional bounded graph search over opaque point-valued edges.
// This is a graph-path adaptation, not the eager all-time-slot CSP scheduler.
// A provider must exhaust the raw domain and resolve every unfiltered candidate
// before degree zero/one is reported. No state value is parsed here.
export function lazyPointPath(provider,{maxDepth=4,nodeCap=20000,stateCap=200000,seed=31}={}){
 if(!Number.isInteger(maxDepth)||maxDepth<0||!Number.isInteger(nodeCap)||nodeCap<0||!Number.isInteger(stateCap)||stateCap<2)throw Error('Invalid lazy search bounds.');
 if(provider.reversible!==true)throw Error('Bidirectional search requires a verified reversible provider.');
 const stats={nodes:0,attempts:0,forced:0,branches:0,graphBuilds:0,peakIncidences:0,generatedStates:2,generatedEdges:0,domainCacheHits:0,rawCandidates:0,markingEliminations:0,authorRejections:0,markingVersions:0,replayedDomains:0,peakFrontier:2};
 const domains=new Map();let version=provider.version(),randomState=seed>>>0;
 function mismatch(c,boundary){return [...c.m].some(([p,v])=>boundary.has(p)&&boundary.get(p)!==v);}
 function refresh(domain){
  stats.graphBuilds++;
  const forward=new Map([[domain.point,[]]]),reverse=new Map();
  for(const entry of domain.accepted){const c=provider.decorate(entry.raw);if(mismatch(c,domain.boundary))throw Error('Learned rule rejects an accepted prefix edge.');forward.get(domain.point).push(c.id);reverse.set(c.id,[domain.point]);}
  domain.forward=forward;domain.reverse=reverse;stats.peakIncidences=Math.max(stats.peakIncidences,reverse.size);
 }
 function replay(){
  version=provider.version();stats.markingVersions=version;
  for(const domain of domains.values()){refresh(domain);stats.replayedDomains++;}
 }
 function domain(key){
  if(domains.has(key)){stats.domainCacheHits++;return domains.get(key);}
  const raw=provider.domain(key);
  if(raw.complete!==true)return {unknown:true,reason:raw.reason||'incomplete-candidate-domain'};
  const d={point:raw.point,boundary:raw.boundary,accepted:[]};stats.rawCandidates+=raw.candidates.length;
  for(const entry of raw.candidates){
   const c=provider.decorate(entry);
   if(mismatch(c,d.boundary)){stats.markingEliminations++;continue;}
   // Authors resolve geometry; the algorithm sees only opaque destinations.
   const result=provider.resolve(entry);stats.attempts++;
   if(result?.unknown)return {unknown:true,reason:result.reason};
   if(!result){stats.authorRejections++;provider.observeRejected?.(entry);if(provider.version()!==version){replay();refresh(d);}continue;}
   if(c.t.size!==1||c.t.get(d.point)!==1)throw Error('Path candidate must cover its one complete root obligation.');
   d.accepted.push({raw:entry,id:c.id,destination:result.key});
  }
  refresh(d);domains.set(key,d);
  return d;
 }
 const seen=[new Map([[provider.sourceKey,{distance:0,parent:null,edge:null}]]),new Map([[provider.targetKey,{distance:0,parent:null,edge:null}]])];
 let frontiers=[[provider.sourceKey],[provider.targetKey]],levels=[0,0];
 function answer(meeting){
  const paths=[[],[]];for(let side=0;side<2;side++){let k=meeting;while(seen[side].get(k).parent!==null){const n=seen[side].get(k);paths[side].push(n.edge);k=n.parent;}paths[side].reverse();}
  return{status:'equivalent',meeting,leftPath:paths[0],rightPath:paths[1],distance:paths[0].length+paths[1].length,stats};
 }
 if(provider.sourceKey===provider.targetKey)return answer(provider.sourceKey);
 while(levels[0]+levels[1]<maxDepth){
  const side=levels[0]<=levels[1]?0:1,other=1-side,next=[];
  for(const key of frontiers[side]){
   if(stats.nodes>=nodeCap)return{status:'unknown',reason:'search-node-budget',stats};
   stats.nodes++;const d=domain(key);if(d.unknown)return{status:'unknown',reason:d.reason,stats};
   const options=[...d.accepted];
   if(options.length===1)stats.forced++;else if(options.length>1)stats.branches++;
   // Seeded neutral candidate permutation; no geometry or type preference.
   for(let i=options.length-1;i>0;i--){randomState=(1664525*randomState+1013904223)>>>0;const j=Math.floor(randomState/4294967296*(i+1));[options[i],options[j]]=[options[j],options[i]];}
   for(const edge of options){
    stats.generatedEdges++;const destination=edge.destination,distance=levels[side]+1;
    if(!seen[side].has(destination)){
     if(seen[0].size+seen[1].size>=stateCap)return{status:'unknown',reason:'search-state-budget',stats};
     seen[side].set(destination,{distance,parent:key,edge:edge.id});next.push(destination);stats.generatedStates++;
    }
    if(seen[other].has(destination)&&seen[side].get(destination).distance+seen[other].get(destination).distance<=maxDepth)return answer(destination);
   }
  }
  frontiers[side]=next;levels[side]++;stats.peakFrontier=Math.max(stats.peakFrontier,frontiers[0].length+frontiers[1].length);
  if(!next.length)return{status:'exhausted-finite-search',stats};
 }
 return{status:'exhausted-finite-search',stats};
}
