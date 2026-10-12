import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { onlinePointSearch, pointSearch } from '../apps/knot-movie/point-search.mjs';
import { solve, parse, canonical, moves, verifyMovie, examples } from '../apps/knot-movie/engine.mjs';
import { trefoilIdentification } from '../apps/knot-movie/cases.mjs';
const nodeSource=readFileSync(new URL('../apps/knot-movie/point-search.mjs',import.meta.url),'utf8');
assert(!/\b(?:import|colorDimension|canonical|Reidemeister|crossingCap|\.kind)\b/.test(nodeSource),'Point engine must have no knot-specific dependencies.');
function model(inequality=false) {
  const tiles=[];
  for(let p=0;p<3;p++) for(let a=0;a<3;a++)for(let b=0;b<3;b++){
    const accept=inequality?a!==b:p===2?(a<2&&b<2?a!==b:a===2&&b===2):a===b;
    if(accept)tiles.push({id:tiles.length,t:new Map([[p,1]]),m:new Map([[['a','b','c'][p],a],[['b','c','a'][p],b]])});
  }
  return {depth:3,sourceKey:'opaque-start',targetKey:'opaque-end',tiles};
}
const cat=model(),plain=onlinePointSearch(cat,{learn:false,seed:null}),live=onlinePointSearch(cat,{seed:null});
assert.equal(plain.status,'equivalent');assert.equal(live.status,plain.status);
assert(live.learning.failures>0);assert.equal(live.learning.initialAssignedValues,0);
assert(live.stats.learnedMarkingEliminations>0,'Activated markings must remove live candidates through the graph.');
for(const e of live.learning.events.filter(x=>x.marking))assert.equal(pointSearch(cat,{initialSelected:[e.candidate]}).status,'exhausted-finite-search');
assert.deepEqual(onlinePointSearch(cat,{seed:null}).learning.events.map(x=>x.marking),live.learning.events.map(x=>x.marking),'No cross-run marks.');
const decorated={...cat,tiles:cat.tiles.map(x=>({...x,kind:'misleading',crossingCount:999}))};
assert.deepEqual(onlinePointSearch(decorated).selected,onlinePointSearch(cat).selected,'Semantic metadata cannot change the search.');
const dead=onlinePointSearch({depth:2,tiles:[{id:0,t:new Map([[0,1]]),m:new Map()}]});assert.equal(dead.status,'exhausted-finite-search');assert.equal(dead.stats.forced,0);
const shared=onlinePointSearch({depth:2,tiles:[{id:0,t:new Map([[0,1],[1,1]]),m:new Map()}]});assert.deepEqual(shared.selected,[0]);assert.equal(shared.stats.forced,1);
const fractional=onlinePointSearch({depth:2,tiles:[{id:0,t:new Map([[0,.5],[1,1]]),m:new Map()}]});assert.equal(fractional.status,'exhausted-finite-search');
const unresolved=onlinePointSearch(cat,{proofNodeCap:0,seed:null});assert.equal(unresolved.status,'equivalent');assert.equal(unresolved.learning.failures,0);assert(unresolved.stats.unresolvedLabels>0);
const contextual=onlinePointSearch(model(true),{seed:null});assert.equal(contextual.status,'equivalent');assert(contextual.stats.contextDependentFailures>0);assert.equal(contextual.learning.failures,0);
assert.equal(onlinePointSearch(cat,{nodeCap:0}).status,'unknown');
const saved=JSON.stringify([...cat.tiles].map(x=>[x.id,[...x.t],[...x.m]]));onlinePointSearch(cat);assert.equal(JSON.stringify([...cat.tiles].map(x=>[x.id,[...x.t],[...x.m]])),saved);
function reachable(w,target,depth,cap){if(canonical(w)===canonical(target))return true;if(!depth)return false;return moves(w,cap).some(m=>reachable(m.after,target,depth-1,cap));}
for(const text of [examples.curl,examples.bigon,'O1+ U1+ O2- U2-'])for(const depth of [1,2])for(const lane of ['baseline','gcts']){
  const w=parse(text),r=solve(w,[],{depth,crossingCap:3,lane});assert.equal(r.status==='equivalent',reachable(w,[],depth,3));assert.equal(r.knotHeuristics,false);if(r.certificate)assert(verifyMovie(r.certificate));
}
const movies=[];
for(const lane of ['baseline','gcts']){const r=solve(parse(trefoilIdentification.source),parse(trefoilIdentification.target),{...trefoilIdentification,lane});assert.equal(r.status,'equivalent');assert.equal(r.certificate.steps.length,3);assert(verifyMovie(r.certificate));movies.push(r.certificate);}
const negative=solve(parse(examples.trefoil),[],{depth:2,crossingCap:3,lane:'gcts'});assert.notEqual(negative.status,'inequivalent');assert.equal(negative.knotEquivalence,'unknown');
assert.throws(()=>solve(parse(examples.curl),[],{lane:'gcts+rl'}),/legacy/);
console.log(JSON.stringify({passed:true,onlineGuards:live.learning.failures,liveEliminations:live.stats.learnedMarkingEliminations,contextOnlyFailures:contextual.stats.contextDependentFailures,unresolvedLabels:unresolved.stats.unresolvedLabels,trefoilMoves:movies[0].steps.map(x=>x.kind),negativeStatus:negative.status}));
